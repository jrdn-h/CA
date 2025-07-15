"""On-chain metrics loader with Glassnode API integration."""

import requests
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import time

from .crypto_cache import cache_crypto_request, get_cache_manager

logger = logging.getLogger(__name__)


class OnChainLoader:
    """Loads on-chain metrics from multiple providers with intelligent fallback."""
    
    def __init__(self, glassnode_api_key: Optional[str] = None):
        """Initialize with optional Glassnode API key."""
        self.glassnode_api_key = glassnode_api_key
        self.glassnode_base_url = "https://api.glassnode.com/v1/metrics"
        
        # Free tier endpoints that don't require API key
        self.free_endpoints = [
            "addresses/active_count",
            "market/price_usd_close", 
            "market/marketcap_usd",
            "network/hash_rate_mean",
            "transactions/count",
        ]
        
        logger.info(f"🔗 OnChainLoader initialized with {'API key' if glassnode_api_key else 'free tier'}")

    @cache_crypto_request("glassnode_metric", ttl=300)  # Cache for 5 minutes
    def get_glassnode_metric(
        self,
        asset: str,
        metric: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        resolution: str = "1d"
    ) -> pd.DataFrame:
        """Fetch a specific metric from Glassnode."""
        
        # Validate metric endpoint
        if metric not in self.free_endpoints and not self.glassnode_api_key:
            logger.warning(f"⚠️  Metric {metric} requires API key, skipping")
            return pd.DataFrame()
        
        try:
            url = f"{self.glassnode_base_url}/{metric}"
            
            params = {
                "a": asset.lower(),
                "i": resolution,
            }
            
            # Add date range if specified
            if start_date:
                start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
                params["s"] = start_ts
                
            if end_date:
                end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
                params["u"] = end_ts
            
            # Add API key if available
            if self.glassnode_api_key:
                params["api_key"] = self.glassnode_api_key
            
            logger.debug(f"🌐 Fetching Glassnode metric: {metric} for {asset}")
            
            # Respect rate limits
            time.sleep(0.1)
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data:
                    # Convert to DataFrame
                    df = pd.DataFrame(data)
                    df['timestamp'] = pd.to_datetime(df['t'], unit='s')
                    df['date'] = df['timestamp'].dt.date
                    df['value'] = df['v']
                    df = df[['date', 'timestamp', 'value']].sort_values('timestamp')
                    
                    logger.info(f"✅ Fetched {len(df)} data points for {metric}")
                    return df
            else:
                logger.warning(f"⚠️  Glassnode API error {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error fetching {metric} for {asset}: {e}")
            
        return pd.DataFrame()

    def get_active_addresses(self, asset: str, days: int = 30) -> Dict[str, Any]:
        """Get active addresses trend for the asset."""
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        df = self.get_glassnode_metric(
            asset, "addresses/active_count", start_date, end_date
        )
        
        if df.empty:
            return {"error": "No active addresses data available"}
        
        latest = df.iloc[-1]['value'] if not df.empty else 0
        avg_30d = df['value'].mean() if len(df) > 1 else latest
        trend = "increasing" if latest > avg_30d else "decreasing"
        
        return {
            "current_active_addresses": int(latest),
            "30d_average": int(avg_30d),
            "trend": trend,
            "data_points": len(df),
            "timeframe": f"{start_date} to {end_date}"
        }

    def get_network_health(self, asset: str) -> Dict[str, Any]:
        """Get comprehensive network health metrics."""
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        metrics = {}
        
        # Hash rate (for Bitcoin)
        if asset.upper() in ["BTC", "BITCOIN"]:
            hash_rate_df = self.get_glassnode_metric(
                asset, "network/hash_rate_mean", start_date, end_date
            )
            if not hash_rate_df.empty:
                latest_hash_rate = hash_rate_df.iloc[-1]['value']
                metrics["hash_rate_th"] = f"{latest_hash_rate / 1e18:.2f}"  # Convert to TH/s
        
        # Transaction count
        tx_count_df = self.get_glassnode_metric(
            asset, "transactions/count", start_date, end_date
        )
        if not tx_count_df.empty:
            avg_tx_count = tx_count_df['value'].mean()
            metrics["avg_daily_transactions"] = int(avg_tx_count)
        
        # Active addresses
        addresses_data = self.get_active_addresses(asset, 7)
        if "error" not in addresses_data:
            metrics["active_addresses"] = addresses_data["current_active_addresses"]
            metrics["address_trend"] = addresses_data["trend"]
        
        metrics["health_score"] = self._calculate_health_score(metrics)
        
        return metrics

    def _calculate_health_score(self, metrics: Dict[str, Any]) -> str:
        """Calculate a simple network health score."""
        score = 0
        
        # Higher transaction count = healthier
        if metrics.get("avg_daily_transactions", 0) > 100000:
            score += 2
        elif metrics.get("avg_daily_transactions", 0) > 50000:
            score += 1
        
        # Increasing address trend = healthier
        if metrics.get("address_trend") == "increasing":
            score += 2
        elif metrics.get("address_trend") == "stable":
            score += 1
        
        # Hash rate presence (for Bitcoin) = healthier
        if "hash_rate_th" in metrics:
            score += 1
        
        if score >= 4:
            return "Excellent"
        elif score >= 2:
            return "Good"
        else:
            return "Concerning"

    def get_market_indicators(self, asset: str) -> Dict[str, Any]:
        """Get market-specific on-chain indicators."""
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        indicators = {}
        
        # Market cap from Glassnode
        mcap_df = self.get_glassnode_metric(
            asset, "market/marketcap_usd", start_date, end_date
        )
        if not mcap_df.empty:
            latest_mcap = mcap_df.iloc[-1]['value']
            indicators["market_cap_usd"] = f"${latest_mcap:,.0f}"
        
        # Price validation from Glassnode
        price_df = self.get_glassnode_metric(
            asset, "market/price_usd_close", start_date, end_date
        )
        if not price_df.empty:
            latest_price = price_df.iloc[-1]['value']
            week_ago_price = price_df.iloc[-7]['value'] if len(price_df) >= 7 else latest_price
            price_change_7d = ((latest_price - week_ago_price) / week_ago_price) * 100
            
            indicators["price_usd"] = f"${latest_price:,.2f}"
            indicators["price_change_7d_pct"] = f"{price_change_7d:+.2f}%"
        
        return indicators

    def get_comprehensive_analysis(self, asset: str) -> Dict[str, Any]:
        """Get a comprehensive on-chain analysis for the asset."""
        logger.info(f"🔍 Running comprehensive on-chain analysis for {asset}")
        
        analysis = {
            "asset": asset.upper(),
            "timestamp": datetime.now().isoformat(),
            "data_sources": ["Glassnode"],
        }
        
        # Network health
        network_health = self.get_network_health(asset)
        analysis["network_health"] = network_health
        
        # Market indicators  
        market_indicators = self.get_market_indicators(asset)
        analysis["market_indicators"] = market_indicators
        
        # Active addresses
        address_metrics = self.get_active_addresses(asset)
        analysis["address_metrics"] = address_metrics
        
        # Generate summary
        health_score = network_health.get("health_score", "Unknown")
        tx_count = network_health.get("avg_daily_transactions", 0)
        
        analysis["summary"] = f"""
{asset.upper()} On-Chain Analysis Summary:
- Network Health: {health_score}
- Daily Transactions: {tx_count:,.0f}
- Address Activity: {address_metrics.get('trend', 'Unknown')}
- Current Active Addresses: {address_metrics.get('current_active_addresses', 'N/A')}
        """.strip()
        
        logger.info(f"✅ Comprehensive analysis complete for {asset}")
        return analysis


# Global instance for easy access
_onchain_loader = None


def get_onchain_loader(api_key: Optional[str] = None) -> OnChainLoader:
    """Get or create the global on-chain loader instance."""
    global _onchain_loader
    if _onchain_loader is None:
        _onchain_loader = OnChainLoader(api_key)
    return _onchain_loader 