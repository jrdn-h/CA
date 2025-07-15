"""Command-line interface for TradingAgents operations dashboard."""

import click
import asyncio
import logging
import sys
from pathlib import Path

from .dashboard_server import get_dashboard_server
from .metrics_collector import get_metrics_collector
from .health_monitor import HealthMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """TradingAgents Operations Dashboard CLI."""
    pass


@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind dashboard server')
@click.option('--port', default=8000, help='Port to bind dashboard server')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def dashboard(host: str, port: int, debug: bool):
    """Start the operations dashboard server."""
    click.echo("🚀 Starting TradingAgents Operations Dashboard...")
    
    try:
        # Initialize components
        metrics_collector = get_metrics_collector()
        dashboard_server = get_dashboard_server(host, port)
        
        click.echo(f"📊 Metrics collector initialized")
        click.echo(f"🖥️  Dashboard server starting on http://{host}:{port}")
        click.echo(f"📈 Prometheus metrics: http://{host}:{port}/metrics")
        click.echo(f"❤️  Health check: http://{host}:{port}/health")
        
        # Start server
        dashboard_server.run(debug=debug)
        
    except KeyboardInterrupt:
        click.echo("\\n👋 Dashboard stopped by user")
    except Exception as e:
        click.echo(f"❌ Error starting dashboard: {e}")
        sys.exit(1)


@cli.command()
async def health():
    """Check system health status."""
    click.echo("🔍 Checking TradingAgents system health...")
    
    try:
        monitor = HealthMonitor()
        health_status = await monitor.get_system_health()
        
        status = health_status["status"]
        if status == "healthy":
            click.echo("✅ System status: HEALTHY", color='green')
        elif status == "degraded":
            click.echo("⚠️  System status: DEGRADED", color='yellow')
        else:
            click.echo("❌ System status: UNHEALTHY", color='red')
        
        # Display component details
        components = health_status.get("components", {})
        
        # Redis Cache
        redis_status = components.get("redis_cache", {})
        redis_icon = "✅" if redis_status.get("available") else "❌"
        click.echo(f"  {redis_icon} Redis Cache: {redis_status.get('status', 'unknown')}")
        
        # Exchanges  
        exchange_status = components.get("exchanges", {})
        healthy_exchanges = exchange_status.get("healthy_count", 0)
        total_exchanges = exchange_status.get("total_count", 0)
        exchange_icon = "✅" if healthy_exchanges >= total_exchanges * 0.8 else "⚠️" if healthy_exchanges >= total_exchanges * 0.6 else "❌"
        click.echo(f"  {exchange_icon} Exchanges: {healthy_exchanges}/{total_exchanges} healthy")
        
        # Data Providers
        provider_status = components.get("data_providers", {})
        healthy_providers = provider_status.get("healthy_count", 0)
        total_providers = provider_status.get("total_count", 0)
        provider_icon = "✅" if healthy_providers >= total_providers * 0.7 else "⚠️" if healthy_providers >= total_providers * 0.5 else "❌"
        click.echo(f"  {provider_icon} Data Providers: {healthy_providers}/{total_providers} healthy")
        
    except Exception as e:
        click.echo(f"❌ Error checking health: {e}")
        sys.exit(1)


@cli.command()
async def cache_stats():
    """Display cache performance statistics."""
    click.echo("📊 Fetching cache performance statistics...")
    
    try:
        monitor = HealthMonitor()
        stats = await monitor.get_cache_stats()
        
        if not stats.get("available"):
            click.echo("❌ Redis cache is not available")
            return
        
        click.echo("✅ Redis Cache Statistics:")
        click.echo(f"  📈 Hit Ratio: {stats.get('hit_ratio', 0):.1f}%")
        click.echo(f"  🎯 Total Hits: {stats.get('total_hits', 0):,}")
        click.echo(f"  ❌ Total Misses: {stats.get('total_misses', 0):,}")
        click.echo(f"  🔑 Total Keys: {stats.get('total_keys', 0):,}")
        click.echo(f"  💾 Memory Usage: {stats.get('memory_usage_mb', 0):.1f} MB")
        click.echo(f"  👥 Connected Clients: {stats.get('connected_clients', 0)}")
        click.echo(f"  ⏱️  Uptime: {stats.get('uptime_hours', 0):.1f} hours")
        
    except Exception as e:
        click.echo(f"❌ Error getting cache stats: {e}")
        sys.exit(1)


@cli.command()
@click.option('--docker', is_flag=True, help='Use Docker Compose for full monitoring stack')
def start_monitoring(docker: bool):
    """Start the complete monitoring stack."""
    if docker:
        click.echo("🐳 Starting Docker monitoring stack...")
        import subprocess
        try:
            result = subprocess.run([
                'docker-compose', '-f', 'docker-compose.ops.yml', 'up', '-d'
            ], check=True, capture_output=True, text=True)
            
            click.echo("✅ Monitoring stack started successfully!")
            click.echo("📊 Grafana: http://localhost:3000 (admin/tradingagents)")
            click.echo("📈 Prometheus: http://localhost:9090")
            click.echo("🖥️  Dashboard: http://localhost:8000")
            click.echo("🔴 Redis: localhost:6379")
            
        except subprocess.CalledProcessError as e:
            click.echo(f"❌ Error starting Docker stack: {e}")
            click.echo(f"Output: {e.output}")
            sys.exit(1)
    else:
        click.echo("🚀 Starting local monitoring...")
        # Just start the dashboard
        dashboard.callback('0.0.0.0', 8000, False)


@cli.command()
def stop_monitoring():
    """Stop the Docker monitoring stack."""
    click.echo("🛑 Stopping Docker monitoring stack...")
    import subprocess
    try:
        subprocess.run([
            'docker-compose', '-f', 'docker-compose.ops.yml', 'down'
        ], check=True)
        click.echo("✅ Monitoring stack stopped successfully!")
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Error stopping Docker stack: {e}")
        sys.exit(1)


if __name__ == '__main__':
    cli() 