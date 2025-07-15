"""MetricRegistry: Intelligent fallback system for multiple on-chain data providers."""

import logging
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime
import pandas as pd
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

from .onchain_loader import OnChainLoader
from .crypto_cache import get_cache_manager

logger = logging.getLogger(__name__)


class DataProvider:
    """Represents a data provider with priority and capabilities."""
    
    def __init__(self, name: str, priority: int, loader_func: Callable, 
                 available_metrics: List[str], requires_api_key: bool = False):
        self.name = name
        self.priority = priority  # Lower number = higher priority
        self.loader_func = loader_func
        self.available_metrics = available_metrics
        self.requires_api_key = requires_api_key
        self.failure_count = 0
        self.last_success = None
        self.is_healthy = True

    def can_provide(self, metric: str) -> bool:
        """Check if this provider can supply the given metric."""
        return metric in self.available_metrics and self.is_healthy

    def record_success(self):
        """Record a successful data fetch."""
        self.failure_count = 0
        self.last_success = datetime.now()
        self.is_healthy = True

    def record_failure(self):
        """Record a failed data fetch."""
        self.failure_count += 1
        if self.failure_count >= 3:
            self.is_healthy = False
            logger.warning(f"⚠️  Provider {self.name} marked unhealthy after {self.failure_count} failures")

    def reset_health(self):
        """Reset provider health status."""
        self.failure_count = 0
        self.is_healthy = True
        logger.info(f"✅ Provider {self.name} health reset")


class BatchOptimizer:
    """Optimizes batch requests by grouping compatible metrics by provider."""
    
    @staticmethod
    def group_by_provider(requests: List[Tuple[str, str]], providers: List[DataProvider]) -> Dict[str, List[Tuple[str, str]]]:
        """Group requests by the best available provider for each metric."""
        provider_groups = {}
        
        for metric, asset in requests:
            # Find best provider for this metric
            available_providers = [p for p in providers if p.can_provide(metric)]
            if available_providers:
                # Sort by priority and health
                available_providers.sort(key=lambda x: (x.priority, x.failure_count))
                best_provider = available_providers[0]
                
                if best_provider.name not in provider_groups:
                    provider_groups[best_provider.name] = []
                provider_groups[best_provider.name].append((metric, asset))
        
        return provider_groups

    @staticmethod
    def optimize_cache_keys(requests: List[Tuple[str, str]]) -> List[Tuple[str, Dict[str, Any]]]:
        """Convert metric requests to cache-compatible format."""
        cache_requests = []
        for metric, asset in requests:
            cache_key = f"metric_{metric}"
            cache_params = {"asset": asset, "metric": metric}
            cache_requests.append((cache_key, cache_params))
        return cache_requests

    @staticmethod
    def detect_redundant_requests(requests: List[Tuple[str, str]]) -> Tuple[List[Tuple[str, str]], Dict[str, str]]:
        """Detect and eliminate redundant requests, returning unique requests and a mapping."""
        unique_requests = []
        redundancy_map = {}
        seen = set()
        
        for metric, asset in requests:
            request_key = f"{metric}:{asset}"
            if request_key not in seen:
                unique_requests.append((metric, asset))
                seen.add(request_key)
            else:
                # Map this to the first occurrence
                redundancy_map[request_key] = request_key
                
        return unique_requests, redundancy_map


class MetricRegistry:
    """Enhanced registry with batch optimization and intelligent caching."""
    
    def __init__(self):
        self.providers: List[DataProvider] = []
        self.cache = get_cache_manager()
        self.batch_optimizer = BatchOptimizer()
        self.batch_stats = {
            'total_batch_requests': 0,
            'cache_hits_in_batch': 0,
            'provider_calls_saved': 0,
            'average_batch_size': 0,
            'concurrent_requests': 0
        }
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize available data providers in priority order."""
        
        # Provider 1: Glassnode (highest priority, most comprehensive)
        glassnode_metrics = [
            "active_addresses", "hash_rate", "transactions_count", 
            "market_cap", "price", "nvt_ratio", "mvrv_ratio",
            "exchange_flows", "whale_activity", "hodl_waves"
        ]
        glassnode_loader = lambda metric, asset, **kwargs: self._fetch_glassnode(metric, asset, **kwargs)
        self.providers.append(DataProvider(
            "Glassnode", 1, glassnode_loader, glassnode_metrics, requires_api_key=True
        ))

        # Provider 2: IntoTheBlock (secondary, good for whale metrics)
        intotheblock_metrics = [
            "active_addresses", "large_transactions", "whale_activity",
            "price", "market_cap", "transaction_volume"
        ]
        itb_loader = lambda metric, asset, **kwargs: self._fetch_intotheblock(metric, asset, **kwargs)
        self.providers.append(DataProvider(
            "IntoTheBlock", 2, itb_loader, intotheblock_metrics, requires_api_key=True
        ))

        # Provider 3: Dune Analytics (third, good for DeFi metrics)
        dune_metrics = [
            "defi_tvl", "dex_volume", "lending_activity", 
            "staking_metrics", "governance_activity"
        ]
        dune_loader = lambda metric, asset, **kwargs: self._fetch_dune(metric, asset, **kwargs)
        self.providers.append(DataProvider(
            "Dune", 3, dune_loader, dune_metrics, requires_api_key=True
        ))

        # Provider 4: Mock/Demo Provider (always available, fallback)
        mock_metrics = [
            "active_addresses", "hash_rate", "transactions_count",
            "market_cap", "price", "network_health", "whale_activity"
        ]
        mock_loader = lambda metric, asset, **kwargs: self._fetch_mock_data(metric, asset, **kwargs)
        self.providers.append(DataProvider(
            "MockProvider", 99, mock_loader, mock_metrics, requires_api_key=False
        ))

        logger.info(f"🔗 MetricRegistry initialized with {len(self.providers)} providers")

    def get_metric(self, metric: str, asset: str, **kwargs) -> Optional[Any]:
        """Get a metric with intelligent fallback through providers."""
        
        # Sort providers by priority and health
        available_providers = [p for p in self.providers if p.can_provide(metric)]
        available_providers.sort(key=lambda x: (x.priority, x.failure_count))

        if not available_providers:
            logger.error(f"❌ No providers available for metric: {metric}")
            return None

        logger.debug(f"🔍 Fetching {metric} for {asset} with {len(available_providers)} providers")

        for provider in available_providers:
            try:
                logger.debug(f"   Trying {provider.name}...")
                result = provider.loader_func(metric, asset, **kwargs)
                
                if result is not None and not (isinstance(result, pd.DataFrame) and result.empty):
                    provider.record_success()
                    logger.info(f"✅ {metric} fetched successfully from {provider.name}")
                    return result
                else:
                    logger.debug(f"   {provider.name} returned empty result")
                    
            except Exception as e:
                logger.warning(f"⚠️  {provider.name} failed for {metric}: {e}")
                provider.record_failure()
                continue

        logger.error(f"❌ All providers failed for {metric} on {asset}")
        return None

    def get_metrics_batch(self, requests: List[Tuple[str, str]], use_cache: bool = True, 
                         max_concurrent: int = 5) -> Dict[str, Any]:
        """
        Efficiently fetch multiple metrics using batch optimization and caching.
        
        Args:
            requests: List of (metric, asset) tuples
            use_cache: Whether to use cache for optimization
            max_concurrent: Maximum number of concurrent provider calls
            
        Returns:
            Dictionary mapping request_id to results
        """
        if not requests:
            return {}
        
        self.batch_stats['total_batch_requests'] += 1
        self.batch_stats['average_batch_size'] = (
            (self.batch_stats['average_batch_size'] * (self.batch_stats['total_batch_requests'] - 1) + len(requests)) 
            / self.batch_stats['total_batch_requests']
        )
        
        logger.info(f"🚀 Starting batch request for {len(requests)} metrics")
        
        results = {}
        remaining_requests = []
        
        # Step 1: Check cache for existing data
        if use_cache:
            cache_requests = self.batch_optimizer.optimize_cache_keys(requests)
            cached_results = self.cache.get_batch(cache_requests)
            
            for i, (metric, asset) in enumerate(requests):
                request_id = f"{metric}:{asset}"
                cache_key = f"metric_{metric}:{hash(str({'asset': asset, 'metric': metric}))}"
                
                if cache_key in cached_results and cached_results[cache_key] is not None:
                    results[request_id] = cached_results[cache_key]['data']
                    self.batch_stats['cache_hits_in_batch'] += 1
                    logger.debug(f"📦 Cache hit for {metric}:{asset}")
                else:
                    remaining_requests.append((metric, asset))
        else:
            remaining_requests = requests
        
        # Step 2: Optimize remaining requests
        if remaining_requests:
            unique_requests, redundancy_map = self.batch_optimizer.detect_redundant_requests(remaining_requests)
            provider_groups = self.batch_optimizer.group_by_provider(unique_requests, self.providers)
            
            logger.info(f"🔧 Optimized {len(remaining_requests)} → {len(unique_requests)} unique requests across {len(provider_groups)} providers")
            
            # Step 3: Execute requests by provider group with concurrency control
            fresh_results = self._execute_provider_batches(provider_groups, max_concurrent)
            
            # Step 4: Cache fresh results
            if use_cache and fresh_results:
                cache_items = []
                for request_id, data in fresh_results.items():
                    if data is not None:
                        metric, asset = request_id.split(':')
                        cache_key = f"metric_{metric}"
                        cache_params = {"asset": asset, "metric": metric}
                        cache_items.append((cache_key, data, cache_params, None))  # Use smart TTL
                
                if cache_items:
                    cached_count = self.cache.set_batch(cache_items)
                    logger.debug(f"💾 Cached {cached_count} fresh results")
            
            # Merge fresh results
            results.update(fresh_results)
        
        # Calculate optimization savings
        saved_calls = len(requests) - len(remaining_requests)
        self.batch_stats['provider_calls_saved'] += saved_calls
        
        logger.info(f"✅ Batch complete: {len(results)}/{len(requests)} successful, {saved_calls} API calls saved")
        return results

    def _execute_provider_batches(self, provider_groups: Dict[str, List[Tuple[str, str]]], 
                                max_concurrent: int) -> Dict[str, Any]:
        """Execute provider requests with concurrency control."""
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # Submit all provider group tasks
            future_to_provider = {}
            
            for provider_name, provider_requests in provider_groups.items():
                provider = next((p for p in self.providers if p.name == provider_name), None)
                if provider:
                    future = executor.submit(self._execute_provider_batch, provider, provider_requests)
                    future_to_provider[future] = provider_name
            
            # Collect results as they complete
            for future in as_completed(future_to_provider):
                provider_name = future_to_provider[future]
                try:
                    provider_results = future.result()
                    results.update(provider_results)
                    self.batch_stats['concurrent_requests'] += len(provider_results)
                    logger.debug(f"✅ Provider {provider_name} batch completed: {len(provider_results)} results")
                except Exception as e:
                    logger.warning(f"⚠️  Provider {provider_name} batch failed: {e}")
        
        return results

    def _execute_provider_batch(self, provider: DataProvider, requests: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Execute a batch of requests for a single provider."""
        results = {}
        
        for metric, asset in requests:
            request_id = f"{metric}:{asset}"
            try:
                result = provider.loader_func(metric, asset)
                if result is not None:
                    results[request_id] = result
                    provider.record_success()
                else:
                    results[request_id] = None
                    
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed for {metric}:{asset}: {e}")
                provider.record_failure()
                results[request_id] = None
        
        return results

    def warm_critical_metrics(self, assets: List[str] = None, 
                            critical_metrics: List[str] = None) -> Dict[str, int]:
        """Proactively warm cache with critical trading metrics."""
        if assets is None:
            assets = ["BTC", "ETH", "ADA", "SOL"]
        
        if critical_metrics is None:
            critical_metrics = [
                "price", "active_addresses", "whale_activity", 
                "exchange_flows", "market_cap", "hash_rate"
            ]
        
        logger.info(f"🔥 Starting cache warming for {len(assets)} assets × {len(critical_metrics)} metrics")
        
        # Generate warming requests
        warming_requests = [
            (metric, asset) for asset in assets for metric in critical_metrics
        ]
        
        def warm_function(endpoint: str, params: Dict[str, Any]) -> Any:
            metric = params.get('metric')
            asset = params.get('asset')
            return self.get_metric(metric, asset)
        
        # Convert to cache warming format
        cache_requests = [
            (f"metric_{metric}", {"asset": asset, "metric": metric})
            for metric, asset in warming_requests
        ]
        
        warmed_count = self.cache.warm_cache(cache_requests, warm_function)
        
        return {
            "total_requests": len(warming_requests),
            "successfully_warmed": warmed_count,
            "cache_coverage": f"{warmed_count}/{len(warming_requests)}"
        }

    def get_batch_optimization_stats(self) -> Dict[str, Any]:
        """Get comprehensive batch optimization statistics."""
        cache_stats = self.cache.get_optimization_stats()
        
        return {
            "batch_performance": {
                "total_batch_requests": self.batch_stats['total_batch_requests'],
                "average_batch_size": round(self.batch_stats['average_batch_size'], 2),
                "cache_hits_in_batch": self.batch_stats['cache_hits_in_batch'],
                "provider_calls_saved": self.batch_stats['provider_calls_saved'],
                "concurrent_requests_processed": self.batch_stats['concurrent_requests'],
            },
            "optimization_efficiency": {
                "api_call_reduction_ratio": (
                    self.batch_stats['provider_calls_saved'] / 
                    max(self.batch_stats['provider_calls_saved'] + self.batch_stats['concurrent_requests'], 1)
                ),
                "batch_cache_hit_ratio": (
                    self.batch_stats['cache_hits_in_batch'] / 
                    max(self.batch_stats['total_batch_requests'], 1)
                )
            },
            "cache_integration": cache_stats,
            "provider_status": self.get_provider_status()
        }

    def get_comprehensive_analysis(self, asset: str) -> Dict[str, Any]:
        """Get comprehensive analysis using best available providers."""
        
        analysis = {
            "asset": asset.upper(),
            "timestamp": datetime.now().isoformat(),
            "data_sources": [],
            "network_health": {},
            "market_indicators": {},
            "address_metrics": {},
            "provider_status": self.get_provider_status()
        }

        # Key metrics to fetch
        key_metrics = [
            "active_addresses",
            "hash_rate", 
            "transactions_count",
            "market_cap",
            "price",
            "whale_activity"
        ]

        # Use batch optimization for comprehensive analysis
        batch_requests = [(metric, asset) for metric in key_metrics]
        batch_results = self.get_metrics_batch(batch_requests)

        successful_providers = set()

        for metric in key_metrics:
            request_id = f"{metric}:{asset}"
            result = batch_results.get(request_id)
            
            if result is not None:
                # Determine which provider succeeded (simplified)
                for provider in self.providers:
                    if provider.last_success and provider.can_provide(metric):
                        successful_providers.add(provider.name)
                        break

                # Store result in appropriate section
                if metric in ["active_addresses"]:
                    if isinstance(result, dict):
                        analysis["address_metrics"] = result
                elif metric in ["hash_rate", "transactions_count"]:
                    if isinstance(result, (int, float, dict)):
                        analysis["network_health"][metric] = result
                elif metric in ["market_cap", "price"]:
                    if isinstance(result, (str, int, float, dict)):
                        analysis["market_indicators"][metric] = result
                elif metric == "whale_activity":
                    analysis["whale_metrics"] = result

        analysis["data_sources"] = list(successful_providers)
        
        # Generate summary
        health_score = "Good" if len(successful_providers) >= 2 else "Limited"
        analysis["summary"] = f"""
{asset.upper()} Multi-Provider Analysis (Batch Optimized):
- Data Sources: {', '.join(successful_providers)}
- Coverage: {len(successful_providers)}/{len(self.providers)} providers
- Reliability: {health_score}
- Batch Efficiency: Enabled
- Last Updated: {datetime.now().strftime('%H:%M:%S')}
        """.strip()

        return analysis

    def get_provider_status(self) -> Dict[str, Any]:
        """Get current status of all providers."""
        status = {}
        
        for provider in self.providers:
            status[provider.name] = {
                "healthy": provider.is_healthy,
                "priority": provider.priority,
                "failure_count": provider.failure_count,
                "last_success": provider.last_success.isoformat() if provider.last_success else None,
                "metrics_count": len(provider.available_metrics),
                "requires_api_key": provider.requires_api_key
            }
        
        return status

    def reset_all_providers(self):
        """Reset health status for all providers."""
        for provider in self.providers:
            provider.reset_health()
        logger.info("🔄 All provider health statuses reset")

    def add_custom_provider(self, name: str, priority: int, loader_func: Callable, 
                          metrics: List[str], requires_api_key: bool = False):
        """Add a custom data provider."""
        provider = DataProvider(name, priority, loader_func, metrics, requires_api_key)
        self.providers.append(provider)
        logger.info(f"➕ Added custom provider: {name}")

    # Provider-specific fetch methods
    def _fetch_glassnode(self, metric: str, asset: str, **kwargs) -> Any:
        """Fetch from Glassnode (real implementation would use API key)."""
        # Simulate Glassnode API call
        # In real implementation, this would use OnChainLoader with API key
        loader = OnChainLoader()  # Would pass API key in real scenario
        
        if metric == "active_addresses":
            return loader.get_active_addresses(asset)
        elif metric == "hash_rate":
            health = loader.get_network_health(asset)
            return health.get("hash_rate_th")
        # ... other Glassnode metrics
        
        return None

    def _fetch_intotheblock(self, metric: str, asset: str, **kwargs) -> Any:
        """Fetch from IntoTheBlock API."""
        # Placeholder for IntoTheBlock integration
        # Would implement actual API calls in production
        if metric == "whale_activity":
            return {
                "large_transactions_24h": 1247,
                "whale_addresses": 1842,
                "top_holders_concentration": "14.2%"
            }
        return None

    def _fetch_dune(self, metric: str, asset: str, **kwargs) -> Any:
        """Fetch from Dune Analytics API."""
        # Placeholder for Dune Analytics integration  
        # Would implement actual GraphQL queries in production
        if metric == "defi_tvl" and asset.upper() == "ETH":
            return {
                "total_value_locked": "$45,600,000,000",
                "protocols_count": 157,
                "top_protocol": "Uniswap"
            }
        return None

    def _fetch_mock_data(self, metric: str, asset: str, **kwargs) -> Any:
        """Fetch mock data (always available fallback)."""
        # Reliable fallback data for testing/demo
        mock_data = {
            "active_addresses": {
                "current_active_addresses": 850000,
                "30d_average": 820000,
                "trend": "increasing",
                "data_source": "MockProvider"
            },
            "hash_rate": "245.7 TH/s",
            "transactions_count": 245000,
            "market_cap": "$2,100,000,000,000",
            "price": "$116,000.00",
            "network_health": "Good",
            "whale_activity": {
                "large_transactions": 1100,
                "accumulation_trend": "increasing"
            }
        }
        
        return mock_data.get(metric)


# Global registry instance
_metric_registry = None


def get_metric_registry() -> MetricRegistry:
    """Get or create the global metric registry instance."""
    global _metric_registry
    if _metric_registry is None:
        _metric_registry = MetricRegistry()
    return _metric_registry 