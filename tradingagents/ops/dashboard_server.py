"""FastAPI dashboard server for TradingAgents operations monitoring."""

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry
import uvicorn
import logging
from typing import Dict, Any
import json
from datetime import datetime

from .metrics_collector import get_metrics_collector
from .health_monitor import HealthMonitor

logger = logging.getLogger(__name__)


class DashboardServer:
    """FastAPI server for operations dashboard and metrics exposure."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        """Initialize dashboard server."""
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="TradingAgents Operations Dashboard",
            description="Real-time monitoring and metrics for TradingAgents infrastructure",
            version="0.3.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self.metrics_collector = get_metrics_collector()
        self.health_monitor = HealthMonitor()
        
        self._setup_routes()
        logger.info(f"🖥️  Dashboard server initialized on {host}:{port}")
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/")
        async def dashboard_home():
            """Main dashboard page."""
            return HTMLResponse(self._get_dashboard_html())
        
        @self.app.get("/metrics")
        async def prometheus_metrics():
            """Prometheus metrics endpoint."""
            try:
                metrics_data = generate_latest(self.metrics_collector.registry)
                return Response(
                    content=metrics_data,
                    media_type=CONTENT_TYPE_LATEST
                )
            except Exception as e:
                logger.error(f"Error generating metrics: {e}")
                raise HTTPException(status_code=500, detail="Error generating metrics")
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            health_status = await self.health_monitor.get_system_health()
            status_code = 200 if health_status["status"] == "healthy" else 503
            return JSONResponse(content=health_status, status_code=status_code)
        
        @self.app.get("/api/metrics/summary")
        async def metrics_summary():
            """Get current metrics summary."""
            try:
                summary = self.metrics_collector.get_current_metrics()
                return JSONResponse(content=summary)
            except Exception as e:
                logger.error(f"Error getting metrics summary: {e}")
                raise HTTPException(status_code=500, detail="Error getting metrics")
        
        @self.app.get("/api/exchanges/status")
        async def exchange_status():
            """Get exchange health status."""
            try:
                status = await self.health_monitor.check_exchange_health()
                return JSONResponse(content=status)
            except Exception as e:
                logger.error(f"Error checking exchange status: {e}")
                raise HTTPException(status_code=500, detail="Error checking exchanges")
        
        @self.app.get("/api/cache/stats")
        async def cache_stats():
            """Get cache performance statistics."""
            try:
                stats = await self.health_monitor.get_cache_stats()
                return JSONResponse(content=stats)
            except Exception as e:
                logger.error(f"Error getting cache stats: {e}")
                raise HTTPException(status_code=500, detail="Error getting cache stats")
    
    def _get_dashboard_html(self) -> str:
        """Generate the main dashboard HTML."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TradingAgents Operations Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .metric-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }
        .metric-title {
            font-size: 18px;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }
        .metric-value {
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }
        .metric-label {
            font-size: 14px;
            color: #666;
        }
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-healthy { background-color: #28a745; }
        .status-warning { background-color: #ffc107; }
        .status-error { background-color: #dc3545; }
        .exchange-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .exchange-card {
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            text-align: center;
        }
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin-bottom: 20px;
        }
        .refresh-btn:hover {
            background: #5a67d8;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 TradingAgents Operations Dashboard</h1>
        <p>Real-time monitoring of crypto infrastructure, caching, and exchange health</p>
    </div>
    
    <button class="refresh-btn" onclick="refreshData()">🔄 Refresh Data</button>
    
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-title">📊 Cache Performance</div>
            <div class="metric-value" id="cache-hit-ratio">--</div>
            <div class="metric-label">Hit Ratio</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">⚡ API Latency</div>
            <div class="metric-value" id="avg-latency">--</div>
            <div class="metric-label">Average Response Time (ms)</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">🏛️ Exchange Health</div>
            <div class="metric-value" id="healthy-exchanges">--</div>
            <div class="metric-label">Healthy Exchanges</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">🔗 Data Providers</div>
            <div class="metric-value" id="providers-up">--</div>
            <div class="metric-label">Providers Online</div>
        </div>
    </div>
    
    <div class="metric-card">
        <div class="metric-title">🏛️ Exchange Status</div>
        <div class="exchange-grid" id="exchange-grid">
            <!-- Exchange cards will be populated here -->
        </div>
    </div>
    
    <script>
        async function refreshData() {
            try {
                // Fetch metrics summary
                const metricsResponse = await fetch('/api/metrics/summary');
                const metrics = await metricsResponse.json();
                
                // Update metrics
                document.getElementById('cache-hit-ratio').textContent = 
                    metrics.cache_metrics.hit_ratio?.toFixed(1) + '%' || '--';
                document.getElementById('avg-latency').textContent = 
                    (metrics.provider_metrics.avg_latency * 1000)?.toFixed(0) + 'ms' || '--';
                document.getElementById('healthy-exchanges').textContent = 
                    `${metrics.exchange_metrics.healthy_exchanges}/${metrics.exchange_metrics.total_exchanges}`;
                document.getElementById('providers-up').textContent = 
                    metrics.provider_metrics.providers_up || '--';
                
                // Fetch exchange status
                const exchangeResponse = await fetch('/api/exchanges/status');
                const exchanges = await exchangeResponse.json();
                
                // Update exchange grid
                const exchangeGrid = document.getElementById('exchange-grid');
                exchangeGrid.innerHTML = '';
                
                for (const [exchange, status] of Object.entries(exchanges)) {
                    const card = document.createElement('div');
                    card.className = 'exchange-card';
                    card.innerHTML = `
                        <div class="status-indicator ${status.healthy ? 'status-healthy' : 'status-error'}"></div>
                        <strong>${exchange.toUpperCase()}</strong><br>
                        <small>${status.latency_ms}ms</small>
                    `;
                    exchangeGrid.appendChild(card);
                }
                
            } catch (error) {
                console.error('Error refreshing data:', error);
            }
        }
        
        // Auto-refresh every 30 seconds
        setInterval(refreshData, 30000);
        
        // Initial load
        refreshData();
    </script>
</body>
</html>
        """
    
    def run(self, debug: bool = False):
        """Start the dashboard server."""
        logger.info(f"🚀 Starting TradingAgents dashboard on http://{self.host}:{self.port}")
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info" if not debug else "debug"
        )


# Global dashboard server instance
_dashboard_server = None

def get_dashboard_server(host: str = "0.0.0.0", port: int = 8000) -> DashboardServer:
    """Get the global dashboard server instance."""
    global _dashboard_server
    if _dashboard_server is None:
        _dashboard_server = DashboardServer(host, port)
    return _dashboard_server 