"""Crypto data caching system with Redis for performance optimization."""

import redis
import json
import hashlib
from typing import Optional, Any, Dict, List, Tuple
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class DataVolatility(Enum):
    """Data volatility levels for smart TTL management."""
    ULTRA_HIGH = "ultra_high"    # 10 seconds
    HIGH = "high"                # 30 seconds
    MEDIUM = "medium"            # 60 seconds
    LOW = "low"                  # 300 seconds
    VERY_LOW = "very_low"        # 900 seconds


class SmartTTLStrategy:
    """Smart TTL strategy based on data type and market conditions."""
    
    # Base TTL mapping by data volatility
    TTL_MAPPING = {
        DataVolatility.ULTRA_HIGH: 10,
        DataVolatility.HIGH: 30,
        DataVolatility.MEDIUM: 60,
        DataVolatility.LOW: 300,
        DataVolatility.VERY_LOW: 900
    }
    
    # Data type to volatility mapping
    DATA_TYPE_VOLATILITY = {
        # Ultra high volatility (real-time trading data)
        'order_book': DataVolatility.ULTRA_HIGH,
        'order_book_depth': DataVolatility.ULTRA_HIGH,
        'live_price': DataVolatility.ULTRA_HIGH,
        'spread_analysis': DataVolatility.ULTRA_HIGH,
        
        # High volatility (frequent price updates)
        'price_data': DataVolatility.HIGH,
        'ohlcv_1m': DataVolatility.HIGH,
        'ohlcv_5m': DataVolatility.HIGH,
        'volume_analysis': DataVolatility.HIGH,
        'arbitrage_opportunities': DataVolatility.HIGH,
        
        # Medium volatility (trading signals)
        'whale_movements': DataVolatility.MEDIUM,
        'exchange_flows': DataVolatility.MEDIUM,
        'ohlcv_1h': DataVolatility.MEDIUM,
        'market_sentiment': DataVolatility.MEDIUM,
        'technical_indicators': DataVolatility.MEDIUM,
        
        # Low volatility (fundamental metrics)
        'network_metrics': DataVolatility.LOW,
        'active_addresses': DataVolatility.LOW,
        'hash_rate': DataVolatility.LOW,
        'transactions_count': DataVolatility.LOW,
        'ohlcv_4h': DataVolatility.LOW,
        'ohlcv_1d': DataVolatility.LOW,
        
        # Very low volatility (historical/static data)
        'market_cap': DataVolatility.VERY_LOW,
        'supply_metrics': DataVolatility.VERY_LOW,
        'token_info': DataVolatility.VERY_LOW,
        'historical_data': DataVolatility.VERY_LOW
    }
    
    @classmethod
    def get_ttl(cls, data_type: str, market_hours: bool = True, high_volatility_period: bool = False) -> int:
        """Get optimal TTL for data type considering market conditions."""
        base_volatility = cls.DATA_TYPE_VOLATILITY.get(data_type, DataVolatility.MEDIUM)
        base_ttl = cls.TTL_MAPPING[base_volatility]
        
        # Adjust TTL based on market conditions
        if not market_hours:
            # Increase TTL during off-hours
            base_ttl = int(base_ttl * 2)
        
        if high_volatility_period:
            # Decrease TTL during high volatility
            base_ttl = max(int(base_ttl * 0.5), 5)  # Minimum 5 seconds
        
        return base_ttl


class CryptoCacheManager:
    """Enhanced cache manager with smart TTL and batch optimization."""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379, 
                 redis_db: int = 0, default_ttl: int = 60):
        """Initialize cache manager with Redis connection."""
        self.default_ttl = default_ttl
        self.redis_client = None
        self.cache_enabled = False
        self.ttl_strategy = SmartTTLStrategy()
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'batch_requests': 0,
            'batch_hits': 0
        }
        
        try:
            self.redis_client = redis.Redis(
                host=redis_host, 
                port=redis_port, 
                db=redis_db,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Test connection
            self.redis_client.ping()
            self.cache_enabled = True
            logger.info(f"✅ Redis cache enabled: {redis_host}:{redis_port}")
        except Exception as e:
            logger.warning(f"⚠️  Redis cache disabled (connection failed): {e}")
            self.cache_enabled = False

    def _generate_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate a consistent cache key from endpoint and parameters."""
        # Sort params for consistent hashing
        sorted_params = sorted(params.items()) if params else []
        key_data = f"{endpoint}:{sorted_params}"
        
        # Use hash for long keys to avoid Redis key length limits
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"crypto_cache:{endpoint}:{key_hash}"

    def _detect_data_type(self, endpoint: str, params: Dict[str, Any] = None) -> str:
        """Intelligently detect data type from endpoint and parameters."""
        endpoint_lower = endpoint.lower()
        
        # Direct mapping for known endpoints
        for data_type in self.ttl_strategy.DATA_TYPE_VOLATILITY.keys():
            if data_type in endpoint_lower:
                return data_type
        
        # Pattern matching for complex endpoints
        if 'order' in endpoint_lower and 'book' in endpoint_lower:
            return 'order_book'
        elif 'ohlcv' in endpoint_lower or 'candle' in endpoint_lower:
            # Determine timeframe if available
            if params and 'timeframe' in params:
                timeframe = params['timeframe']
                return f'ohlcv_{timeframe}'
            return 'ohlcv_1h'  # Default
        elif 'price' in endpoint_lower:
            return 'price_data'
        elif 'whale' in endpoint_lower:
            return 'whale_movements'
        elif 'exchange' in endpoint_lower and 'flow' in endpoint_lower:
            return 'exchange_flows'
        elif 'active' in endpoint_lower and 'address' in endpoint_lower:
            return 'active_addresses'
        elif 'hash' in endpoint_lower and 'rate' in endpoint_lower:
            return 'hash_rate'
        elif 'network' in endpoint_lower:
            return 'network_metrics'
        
        return 'medium_volatility_default'

    def _is_market_hours(self) -> bool:
        """Check if current time is during active trading hours (crypto trades 24/7, but consider US/EU hours)."""
        now = datetime.utcnow()
        # Consider 6 AM to 10 PM UTC as active hours (covers US and EU trading)
        return 6 <= now.hour <= 22

    def _is_high_volatility_period(self) -> bool:
        """Detect if market is in high volatility period (simplified heuristic)."""
        # This could be enhanced with real volatility indicators
        # For now, assume first and last 2 hours of "market day" are high volatility
        now = datetime.utcnow()
        return now.hour in [6, 7, 20, 21]

    def get(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Any]:
        """Retrieve cached data if available and valid."""
        if not self.cache_enabled:
            return None
            
        try:
            cache_key = self._generate_cache_key(endpoint, params or {})
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                self.cache_stats['hits'] += 1
                logger.debug(f"📦 Cache HIT: {endpoint}")
                return data
                
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
        
        self.cache_stats['misses'] += 1
        logger.debug(f"📭 Cache MISS: {endpoint}")
        return None

    def set(self, endpoint: str, data: Any, params: Dict[str, Any] = None, 
            ttl: Optional[int] = None) -> bool:
        """Store data in cache with smart TTL."""
        if not self.cache_enabled:
            return False
            
        try:
            cache_key = self._generate_cache_key(endpoint, params or {})
            
            # Use smart TTL if not specified
            if ttl is None:
                data_type = self._detect_data_type(endpoint, params)
                market_hours = self._is_market_hours()
                high_volatility = self._is_high_volatility_period()
                ttl = self.ttl_strategy.get_ttl(data_type, market_hours, high_volatility)
            
            # Add metadata
            cache_data = {
                "data": data,
                "cached_at": datetime.utcnow().isoformat(),
                "endpoint": endpoint,
                "params": params,
                "data_type": self._detect_data_type(endpoint, params),
                "ttl_used": ttl
            }
            
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(cache_data, default=str)
            )
            
            self.cache_stats['sets'] += 1
            logger.debug(f"💾 Cache SET: {endpoint} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.warning(f"Cache storage error: {e}")
            return False

    def get_batch(self, requests: List[Tuple[str, Dict[str, Any]]]) -> Dict[str, Any]:
        """Retrieve multiple cached items in a single operation."""
        if not self.cache_enabled:
            return {}
        
        self.cache_stats['batch_requests'] += 1
        results = {}
        cache_keys = []
        key_to_request = {}
        
        try:
            # Generate all cache keys
            for endpoint, params in requests:
                cache_key = self._generate_cache_key(endpoint, params or {})
                cache_keys.append(cache_key)
                key_to_request[cache_key] = (endpoint, params)
            
            # Batch retrieve from Redis
            if cache_keys:
                cached_values = self.redis_client.mget(cache_keys)
                
                for cache_key, cached_value in zip(cache_keys, cached_values):
                    endpoint, params = key_to_request[cache_key]
                    request_id = f"{endpoint}:{hash(str(params))}"
                    
                    if cached_value:
                        try:
                            data = json.loads(cached_value)
                            results[request_id] = data
                            self.cache_stats['batch_hits'] += 1
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON in cache for {endpoint}")
                    else:
                        results[request_id] = None
                        
        except Exception as e:
            logger.warning(f"Batch cache retrieval error: {e}")
            
        logger.debug(f"📦 Batch cache: {len(results)} requests, {self.cache_stats['batch_hits']} hits")
        return results

    def set_batch(self, data_items: List[Tuple[str, Any, Dict[str, Any], Optional[int]]]) -> int:
        """Store multiple items in cache efficiently."""
        if not self.cache_enabled:
            return 0
        
        successful_sets = 0
        
        try:
            # Prepare pipeline for batch operations
            pipe = self.redis_client.pipeline()
            
            for endpoint, data, params, ttl in data_items:
                cache_key = self._generate_cache_key(endpoint, params or {})
                
                # Use smart TTL if not specified
                if ttl is None:
                    data_type = self._detect_data_type(endpoint, params)
                    market_hours = self._is_market_hours()
                    high_volatility = self._is_high_volatility_period()
                    ttl = self.ttl_strategy.get_ttl(data_type, market_hours, high_volatility)
                
                # Add metadata
                cache_data = {
                    "data": data,
                    "cached_at": datetime.utcnow().isoformat(),
                    "endpoint": endpoint,
                    "params": params,
                    "data_type": self._detect_data_type(endpoint, params),
                    "ttl_used": ttl
                }
                
                pipe.setex(cache_key, ttl, json.dumps(cache_data, default=str))
            
            # Execute pipeline
            results = pipe.execute()
            successful_sets = sum(1 for result in results if result)
            
            self.cache_stats['sets'] += successful_sets
            logger.debug(f"💾 Batch cache SET: {successful_sets}/{len(data_items)} successful")
            
        except Exception as e:
            logger.warning(f"Batch cache storage error: {e}")
            
        return successful_sets

    def warm_cache(self, critical_endpoints: List[Tuple[str, Dict[str, Any]]], 
                   warm_function: callable) -> int:
        """Proactively warm cache with critical data."""
        if not self.cache_enabled:
            return 0
        
        warmed_count = 0
        logger.info(f"🔥 Starting cache warming for {len(critical_endpoints)} endpoints")
        
        for endpoint, params in critical_endpoints:
            try:
                # Check if already cached
                cached_data = self.get(endpoint, params)
                if cached_data is None:
                    # Fetch fresh data and cache it
                    fresh_data = warm_function(endpoint, params)
                    if fresh_data is not None:
                        if self.set(endpoint, fresh_data, params):
                            warmed_count += 1
                            logger.debug(f"🔥 Warmed cache for {endpoint}")
                        
            except Exception as e:
                logger.warning(f"Cache warming failed for {endpoint}: {e}")
        
        logger.info(f"🔥 Cache warming complete: {warmed_count}/{len(critical_endpoints)} endpoints")
        return warmed_count

    def smart_invalidate(self, patterns: List[str] = None, data_types: List[str] = None,
                        older_than_minutes: int = None) -> int:
        """Intelligent cache invalidation based on patterns, data types, or age."""
        if not self.cache_enabled:
            return 0
        
        total_deleted = 0
        
        try:
            # Get all crypto cache keys
            all_keys = self.redis_client.keys("crypto_cache:*")
            keys_to_delete = []
            
            for key in all_keys:
                should_delete = False
                
                try:
                    # Get cached data to check metadata
                    cached_data = self.redis_client.get(key)
                    if cached_data:
                        data = json.loads(cached_data)
                        
                        # Check data type filter
                        if data_types:
                            cache_data_type = data.get('data_type', '')
                            if cache_data_type in data_types:
                                should_delete = True
                        
                        # Check age filter
                        if older_than_minutes:
                            cached_at = datetime.fromisoformat(data.get('cached_at', ''))
                            age_minutes = (datetime.utcnow() - cached_at).total_seconds() / 60
                            if age_minutes > older_than_minutes:
                                should_delete = True
                        
                        # Check pattern filter
                        if patterns:
                            endpoint = data.get('endpoint', '')
                            for pattern in patterns:
                                if pattern in endpoint:
                                    should_delete = True
                                    break
                    
                    # If no filters specified, delete all
                    if not data_types and not older_than_minutes and not patterns:
                        should_delete = True
                        
                except Exception as e:
                    logger.debug(f"Error checking key {key} for invalidation: {e}")
                    continue
                
                if should_delete:
                    keys_to_delete.append(key)
            
            # Batch delete
            if keys_to_delete:
                total_deleted = self.redis_client.delete(*keys_to_delete)
                
            logger.info(f"🗑️  Smart invalidation: {total_deleted} entries deleted")
            
        except Exception as e:
            logger.warning(f"Smart invalidation error: {e}")
        
        return total_deleted

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get detailed cache performance and optimization statistics."""
        if not self.cache_enabled:
            return {"enabled": False}
        
        try:
            info = self.redis_client.info()
            crypto_keys = len(self.redis_client.keys("crypto_cache:*"))
            
            # Calculate hit ratio
            total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
            hit_ratio = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            # Batch efficiency
            batch_efficiency = (self.cache_stats['batch_hits'] / max(self.cache_stats['batch_requests'], 1))
            
            stats = {
                "enabled": True,
                "performance": {
                    "total_keys": crypto_keys,
                    "hit_ratio_percent": round(hit_ratio, 2),
                    "total_hits": self.cache_stats['hits'],
                    "total_misses": self.cache_stats['misses'],
                    "total_sets": self.cache_stats['sets'],
                    "batch_requests": self.cache_stats['batch_requests'],
                    "batch_efficiency": round(batch_efficiency, 2)
                },
                "redis_info": {
                    "memory_used": info.get("used_memory_human", "Unknown"),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                    "connected_clients": info.get("connected_clients", 0)
                },
                "ttl_strategy": {
                    "smart_ttl_enabled": True,
                    "market_hours_active": self._is_market_hours(),
                    "high_volatility_detected": self._is_high_volatility_period(),
                    "data_type_mappings": len(self.ttl_strategy.DATA_TYPE_VOLATILITY)
                },
                "recommendations": self._get_optimization_recommendations(hit_ratio, batch_efficiency)
            }
            
            return stats
            
        except Exception as e:
            logger.warning(f"Cache stats error: {e}")
            return {"enabled": True, "error": str(e)}

    def _get_optimization_recommendations(self, hit_ratio: float, batch_efficiency: float) -> List[str]:
        """Generate optimization recommendations based on current performance."""
        recommendations = []
        
        if hit_ratio < 70:
            recommendations.append("Consider increasing TTL for stable data types")
        if hit_ratio > 95:
            recommendations.append("TTL might be too long; check data freshness requirements")
        if batch_efficiency < 0.5:
            recommendations.append("Implement more batch requests to improve efficiency")
        if self.cache_stats['batch_requests'] == 0:
            recommendations.append("Start using batch cache operations for better performance")
            
        return recommendations

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching a pattern."""
        if not self.cache_enabled:
            return 0
            
        try:
            keys = self.redis_client.keys(f"crypto_cache:{pattern}*")
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"🗑️  Invalidated {deleted} cache entries matching: {pattern}")
                return deleted
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
            
        return 0

    def clear_all_cache(self) -> bool:
        """Clear all crypto cache entries."""
        if not self.cache_enabled:
            return False
            
        try:
            deleted = self.invalidate_pattern("")
            logger.info(f"🧹 Cleared all crypto cache: {deleted} entries")
            return True
        except Exception as e:
            logger.warning(f"Cache clear error: {e}")
            return False


# Global cache instance
_cache_manager = None


def get_cache_manager() -> CryptoCacheManager:
    """Get or create the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CryptoCacheManager()
    return _cache_manager


def cache_crypto_request(endpoint: str, ttl: int = None, data_type: str = None):
    """Enhanced decorator to cache crypto API requests with smart TTL."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache = get_cache_manager()
            
            # Generate cache params from function arguments
            cache_params = {
                "args": args[1:] if args else [],  # Skip 'self'
                "kwargs": kwargs
            }
            
            # Override data type if specified
            if data_type:
                cache_params["_data_type_override"] = data_type
            
            # Try cache first
            cached_result = cache.get(endpoint, cache_params)
            if cached_result is not None:
                return cached_result.get("data")
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(endpoint, result, cache_params, ttl)
            
            return result
        return wrapper
    return decorator 