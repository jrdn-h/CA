"""Health monitoring system for TradingAgents infrastructure components."""

import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from ..dataflows.crypto_cache import get_cache_manager
from ..dataflows.ccxt_adapters import CCXTAdapters  
from ..dataflows.metric_registry import get_metric_registry

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Monitors health and performance of TradingAgents infrastructure."""
    
    def __init__(self):
        """Initialize health monitor."""
        self.cache_manager = get_cache_manager()
        self.ccxt_adapters = CCXTAdapters()
        self.metric_registry = get_metric_registry()
        
        # Health check intervals
        self.exchange_check_interval = 60  # seconds
        self.provider_check_interval = 120  # seconds
        
        # Health status cache
        self._last_exchange_check = None
        self._last_provider_check = None
        self._exchange_health = {}
        self._provider_health = {}
        
        logger.info("🔍 HealthMonitor initialized")
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        try:
            # Check critical components
            redis_healthy = self.cache_manager.is_redis_available()
            exchange_health = await self.check_exchange_health()
            provider_health = await self.check_provider_health()
            
            # Calculate overall health
            healthy_exchanges = sum(1 for status in exchange_health.values() if status.get('healthy', False))
            total_exchanges = len(exchange_health)
            healthy_providers = sum(1 for status in provider_health.values() if status.get('healthy', False))
            total_providers = len(provider_health)
            
            # Determine overall status
            exchange_ratio = healthy_exchanges / max(1, total_exchanges)
            provider_ratio = healthy_providers / max(1, total_providers)
            
            if redis_healthy and exchange_ratio >= 0.8 and provider_ratio >= 0.7:
                overall_status = "healthy"
            elif exchange_ratio >= 0.6 and provider_ratio >= 0.5:
                overall_status = "degraded"
            else:
                overall_status = "unhealthy"
            
            return {
                "status": overall_status,
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "redis_cache": {
                        "status": "healthy" if redis_healthy else "unhealthy",
                        "available": redis_healthy
                    },
                    "exchanges": {
                        "status": "healthy" if exchange_ratio >= 0.8 else "degraded" if exchange_ratio >= 0.6 else "unhealthy",
                        "healthy_count": healthy_exchanges,
                        "total_count": total_exchanges,
                        "ratio": exchange_ratio
                    },
                    "data_providers": {
                        "status": "healthy" if provider_ratio >= 0.7 else "degraded" if provider_ratio >= 0.5 else "unhealthy", 
                        "healthy_count": healthy_providers,
                        "total_count": total_providers,
                        "ratio": provider_ratio
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def check_exchange_health(self) -> Dict[str, Any]:
        """Check health status of all supported exchanges."""
        now = datetime.now()
        
        # Use cached results if recent
        if (self._last_exchange_check and 
            (now - self._last_exchange_check).seconds < self.exchange_check_interval):
            return self._exchange_health
        
        health_status = {}
        supported_exchanges = ['binance', 'coinbase', 'kraken', 'okx', 'huobi']
        
        for exchange in supported_exchanges:
            try:
                start_time = time.time()
                
                # Test basic connectivity with a simple ticker request
                test_data = self.ccxt_adapters.get_ohlcv_data(
                    exchange, 'BTC/USDT', '1d', 1
                )
                
                latency_ms = (time.time() - start_time) * 1000
                
                # Check if we got valid data
                is_healthy = (
                    test_data is not None and 
                    len(test_data) > 0 and
                    latency_ms < 10000  # Less than 10 seconds
                )
                
                health_status[exchange] = {
                    "healthy": is_healthy,
                    "latency_ms": round(latency_ms, 2),
                    "last_check": now.isoformat(),
                    "status": "operational" if is_healthy else "degraded"
                }
                
            except Exception as e:
                logger.warning(f"Health check failed for {exchange}: {e}")
                health_status[exchange] = {
                    "healthy": False,
                    "latency_ms": None,
                    "last_check": now.isoformat(),
                    "status": "error",
                    "error": str(e)
                }
        
        self._exchange_health = health_status
        self._last_exchange_check = now
        return health_status
    
    async def check_provider_health(self) -> Dict[str, Any]:
        """Check health status of data providers."""
        now = datetime.now()
        
        # Use cached results if recent
        if (self._last_provider_check and 
            (now - self._last_provider_check).seconds < self.provider_check_interval):
            return self._provider_health
        
        health_status = {}
        
        # Check Glassnode provider
        try:
            start_time = time.time()
            
            # Test with a basic metric
            test_metrics = self.metric_registry.get_metric('active_addresses', 'BTC')
            latency_ms = (time.time() - start_time) * 1000
            
            is_healthy = test_metrics is not None
            
            health_status['glassnode'] = {
                "healthy": is_healthy,
                "latency_ms": round(latency_ms, 2),
                "last_check": now.isoformat(),
                "provider_type": "onchain_analytics",
                "status": "operational" if is_healthy else "degraded"
            }
            
        except Exception as e:
            logger.warning(f"Health check failed for Glassnode: {e}")
            health_status['glassnode'] = {
                "healthy": False,
                "latency_ms": None,
                "last_check": now.isoformat(),
                "provider_type": "onchain_analytics",
                "status": "error",
                "error": str(e)
            }
        
        # Check CoinGecko (if available)
        try:
            from ..dataflows.crypto_utils import CryptoUtils
            crypto_utils = CryptoUtils()
            
            start_time = time.time()
            test_data = crypto_utils.get_crypto_data('bitcoin')
            latency_ms = (time.time() - start_time) * 1000
            
            is_healthy = test_data is not None
            
            health_status['coingecko'] = {
                "healthy": is_healthy,
                "latency_ms": round(latency_ms, 2),
                "last_check": now.isoformat(),
                "provider_type": "market_data", 
                "status": "operational" if is_healthy else "degraded"
            }
            
        except Exception as e:
            logger.warning(f"Health check failed for CoinGecko: {e}")
            health_status['coingecko'] = {
                "healthy": False,
                "latency_ms": None,
                "last_check": now.isoformat(),
                "provider_type": "market_data",
                "status": "error",
                "error": str(e)
            }
        
        self._provider_health = health_status
        self._last_provider_check = now
        return health_status
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get Redis cache performance statistics."""
        try:
            if not self.cache_manager.is_redis_available():
                return {
                    "available": False,
                    "status": "redis_unavailable"
                }
            
            # Get basic cache info
            info = self.cache_manager.redis_client.info()
            
            # Calculate hit ratio from Redis stats
            keyspace_hits = info.get('keyspace_hits', 0)
            keyspace_misses = info.get('keyspace_misses', 0)
            total_commands = keyspace_hits + keyspace_misses
            
            hit_ratio = (keyspace_hits / max(1, total_commands)) * 100
            
            return {
                "available": True,
                "hit_ratio": round(hit_ratio, 2),
                "total_hits": keyspace_hits,
                "total_misses": keyspace_misses,
                "total_keys": info.get('db0', {}).get('keys', 0) if 'db0' in info else 0,
                "memory_usage_mb": round(info.get('used_memory', 0) / 1024 / 1024, 2),
                "connected_clients": info.get('connected_clients', 0),
                "uptime_hours": round(info.get('uptime_in_seconds', 0) / 3600, 1),
                "status": "operational"
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "available": False,
                "status": "error",
                "error": str(e)
            }
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for all monitored components."""
        try:
            system_health = await self.get_system_health()
            cache_stats = await self.get_cache_stats()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_status": system_health["status"],
                "cache_performance": {
                    "hit_ratio": cache_stats.get("hit_ratio", 0),
                    "memory_usage_mb": cache_stats.get("memory_usage_mb", 0),
                    "status": cache_stats.get("status", "unknown")
                },
                "exchange_performance": {
                    "healthy_count": system_health["components"]["exchanges"]["healthy_count"],
                    "total_count": system_health["components"]["exchanges"]["total_count"],
                    "average_latency": await self._calculate_average_exchange_latency()
                },
                "provider_performance": {
                    "healthy_count": system_health["components"]["data_providers"]["healthy_count"],
                    "total_count": system_health["components"]["data_providers"]["total_count"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "error",
                "error": str(e)
            }
    
    async def _calculate_average_exchange_latency(self) -> float:
        """Calculate average latency across healthy exchanges."""
        if not self._exchange_health:
            return 0.0
        
        healthy_latencies = [
            status.get("latency_ms", 0) for status in self._exchange_health.values()
            if status.get("healthy", False) and status.get("latency_ms") is not None
        ]
        
        return round(sum(healthy_latencies) / max(1, len(healthy_latencies)), 2) 