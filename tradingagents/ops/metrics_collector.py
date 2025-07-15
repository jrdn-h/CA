"""Prometheus metrics collector for TradingAgents operations monitoring."""

import time
import threading
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry
import logging

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and exposes operational metrics for TradingAgents infrastructure."""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """Initialize metrics collector with optional custom registry."""
        self.registry = registry or CollectorRegistry()
        self._setup_metrics()
        self._cache_stats = {}
        self._exchange_stats = {}
        self._provider_stats = {}
        self._lock = threading.Lock()
        
        logger.info("🔧 MetricsCollector initialized with Prometheus registry")
    
    def _setup_metrics(self):
        """Initialize all Prometheus metrics."""
        
        # Cache Metrics
        self.cache_hits = Counter(
            'tradingagents_cache_hits_total',
            'Total number of cache hits',
            ['cache_type', 'endpoint'],
            registry=self.registry
        )
        
        self.cache_misses = Counter(
            'tradingagents_cache_misses_total', 
            'Total number of cache misses',
            ['cache_type', 'endpoint'],
            registry=self.registry
        )
        
        self.cache_hit_ratio = Gauge(
            'tradingagents_cache_hit_ratio',
            'Cache hit ratio percentage',
            ['cache_type'],
            registry=self.registry
        )
        
        # Provider Latency Metrics
        self.api_request_duration = Histogram(
            'tradingagents_api_request_duration_seconds',
            'API request duration in seconds',
            ['provider', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.provider_availability = Gauge(
            'tradingagents_provider_availability',
            'Provider availability (1=up, 0=down)',
            ['provider', 'provider_type'],
            registry=self.registry
        )
        
        # Exchange Health Metrics  
        self.exchange_status = Gauge(
            'tradingagents_exchange_status',
            'Exchange operational status (1=healthy, 0=unhealthy)',
            ['exchange', 'market'],
            registry=self.registry
        )
        
        self.exchange_latency = Gauge(
            'tradingagents_exchange_latency_ms',
            'Exchange API latency in milliseconds', 
            ['exchange', 'endpoint_type'],
            registry=self.registry
        )
        
        self.order_book_spread = Gauge(
            'tradingagents_order_book_spread_bps',
            'Order book spread in basis points',
            ['exchange', 'symbol'],
            registry=self.registry
        )
        
        # Trading Performance Metrics
        self.strategy_pnl = Gauge(
            'tradingagents_strategy_pnl',
            'Strategy profit and loss',
            ['strategy_name', 'asset', 'timeframe'],
            registry=self.registry
        )
        
        self.sharpe_ratio = Gauge(
            'tradingagents_sharpe_ratio', 
            'Strategy Sharpe ratio',
            ['strategy_name', 'asset', 'timeframe'],
            registry=self.registry
        )
        
        self.max_drawdown = Gauge(
            'tradingagents_max_drawdown',
            'Maximum drawdown percentage',
            ['strategy_name', 'asset', 'timeframe'], 
            registry=self.registry
        )
        
        # System Info
        self.system_info = Info(
            'tradingagents_system_info',
            'System information',
            registry=self.registry
        )
        
        # Set system info
        self.system_info.info({
            'version': '0.3.0',
            'crypto_infrastructure': 'enabled',
            'redis_caching': 'available',
            'exchanges_supported': '5',
            'onchain_providers': '3'
        })
    
    def record_cache_hit(self, cache_type: str, endpoint: str):
        """Record a cache hit."""
        self.cache_hits.labels(cache_type=cache_type, endpoint=endpoint).inc()
        self._update_cache_ratio(cache_type)
    
    def record_cache_miss(self, cache_type: str, endpoint: str):
        """Record a cache miss.""" 
        self.cache_misses.labels(cache_type=cache_type, endpoint=endpoint).inc()
        self._update_cache_ratio(cache_type)
    
    def _update_cache_ratio(self, cache_type: str):
        """Update cache hit ratio calculation."""
        with self._lock:
            hits = self.cache_hits._value.sum()
            misses = self.cache_misses._value.sum()
            total = hits + misses
            
            if total > 0:
                ratio = (hits / total) * 100
                self.cache_hit_ratio.labels(cache_type=cache_type).set(ratio)
    
    def record_api_request(self, provider: str, endpoint: str, duration: float, status: str):
        """Record an API request duration and status."""
        self.api_request_duration.labels(
            provider=provider, 
            endpoint=endpoint, 
            status=status
        ).observe(duration)
    
    def update_provider_status(self, provider: str, provider_type: str, is_available: bool):
        """Update provider availability status."""
        self.provider_availability.labels(
            provider=provider, 
            provider_type=provider_type
        ).set(1 if is_available else 0)
    
    def update_exchange_health(self, exchange: str, market: str, is_healthy: bool, 
                              latency_ms: Optional[float] = None):
        """Update exchange health metrics."""
        self.exchange_status.labels(exchange=exchange, market=market).set(
            1 if is_healthy else 0
        )
        
        if latency_ms is not None:
            self.exchange_latency.labels(
                exchange=exchange, 
                endpoint_type='health_check'
            ).set(latency_ms)
    
    def update_order_book_metrics(self, exchange: str, symbol: str, spread_bps: float):
        """Update order book spread metrics."""
        self.order_book_spread.labels(exchange=exchange, symbol=symbol).set(spread_bps)
    
    def update_strategy_performance(self, strategy_name: str, asset: str, timeframe: str,
                                   pnl: float, sharpe: float, max_dd: float):
        """Update trading strategy performance metrics."""
        self.strategy_pnl.labels(
            strategy_name=strategy_name, 
            asset=asset, 
            timeframe=timeframe
        ).set(pnl)
        
        self.sharpe_ratio.labels(
            strategy_name=strategy_name,
            asset=asset, 
            timeframe=timeframe
        ).set(sharpe)
        
        self.max_drawdown.labels(
            strategy_name=strategy_name,
            asset=asset,
            timeframe=timeframe
        ).set(max_dd)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics summary for dashboard display."""
        with self._lock:
            return {
                'cache_metrics': {
                    'total_hits': self.cache_hits._value.sum(),
                    'total_misses': self.cache_misses._value.sum(),
                    'hit_ratio': self.cache_hit_ratio._value.get()
                },
                'provider_metrics': {
                    'total_requests': self.api_request_duration._value.sum(),
                    'avg_latency': self.api_request_duration._value.sum() / max(1, self.api_request_duration._value.count()),
                    'providers_up': sum(1 for v in self.provider_availability._value.values() if v == 1)
                },
                'exchange_metrics': {
                    'healthy_exchanges': sum(1 for v in self.exchange_status._value.values() if v == 1),
                    'total_exchanges': len(self.exchange_status._value)
                },
                'timestamp': datetime.now().isoformat()
            }


# Global metrics collector instance
_metrics_collector = None

def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector 