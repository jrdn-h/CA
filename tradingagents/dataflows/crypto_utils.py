# Cryptocurrency data utilities - adapted from yfin_utils.py

import requests
from typing import Annotated, Callable, Any, Optional
from pandas import DataFrame
import pandas as pd
from functools import wraps
from datetime import datetime, timedelta
import time
import logging

from .utils import save_output, SavePathType, decorate_all_methods
from .crypto_cache import cache_crypto_request, get_cache_manager

logger = logging.getLogger(__name__)


def init_crypto_client(func: Callable) -> Callable:
    """Decorator to initialize crypto API client and pass it to the function."""

    @wraps(func)
    def wrapper(self, symbol: Annotated[str, "crypto symbol"], *args, **kwargs) -> Any:
        # CoinGecko API base URL (free tier)
        base_url = "https://api.coingecko.com/api/v3"
        # Convert common symbols to CoinGecko IDs
        symbol_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum", 
            "BTC-USD": "bitcoin",
            "ETH-USD": "ethereum",
            "ADA": "cardano",
            "SOL": "solana",
            "DOT": "polkadot",
            "MATIC": "polygon",
        }
        
        # Extract base symbol if it contains -USD
        base_symbol = symbol.replace("-USD", "")
        crypto_id = symbol_map.get(base_symbol.upper(), base_symbol.lower())
        
        return func(self, crypto_id, base_url, *args, **kwargs)

    return wrapper


@decorate_all_methods(init_crypto_client)
class CryptoUtils:
    """Cryptocurrency data utilities using CoinGecko API (free tier)."""

    @cache_crypto_request("market_chart_range", ttl=60)  # Cache for 60 seconds
    def get_crypto_data(
        self,
        crypto_id: str,
        base_url: str,
        start_date: Annotated[
            str, "start date for retrieving crypto price data, YYYY-mm-dd"
        ],
        end_date: Annotated[
            str, "end date for retrieving crypto price data, YYYY-mm-dd"
        ],
        save_path: SavePathType = None,
    ) -> DataFrame:
        """Retrieve crypto price data for designated symbol with intelligent caching."""
        
        try:
            # Convert dates to timestamps
            start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
            end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
            
            # CoinGecko historical data endpoint (free tier has rate limits)
            url = f"{base_url}/coins/{crypto_id}/market_chart/range"
            params = {
                'vs_currency': 'usd',
                'from': start_ts,
                'to': end_ts
            }
            
            logger.debug(f"🌐 Fetching crypto data: {crypto_id} ({start_date} to {end_date})")
            
            # Add small delay to respect rate limits (only when not cached)
            time.sleep(0.1)
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Convert to DataFrame with yfinance-like structure
                prices = data.get('prices', [])
                volumes = data.get('total_volumes', [])
                
                if prices:
                    df_data = []
                    for i, (timestamp, price) in enumerate(prices):
                        volume = volumes[i][1] if i < len(volumes) else 0
                        date = pd.to_datetime(timestamp, unit='ms')
                        df_data.append({
                            'Open': price,
                            'High': price,  # CoinGecko free tier doesn't provide OHLC
                            'Low': price,
                            'Close': price,
                            'Volume': volume
                        })
                    
                    crypto_data = DataFrame(df_data, index=[pd.to_datetime(p[0], unit='ms') for p in prices])
                    crypto_data.index.name = 'Date'
                    logger.info(f"✅ Fetched {len(crypto_data)} data points for {crypto_id}")
                    return crypto_data
            else:
                logger.warning(f"⚠️  API response {response.status_code} for {crypto_id}")
                    
            # Fallback: return empty DataFrame with correct structure
            return DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
            
        except Exception as e:
            logger.error(f"❌ Error fetching crypto data for {crypto_id}: {e}")
            # Return empty DataFrame with correct structure
            return DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])

    @cache_crypto_request("coin_info", ttl=120)  # Cache for 2 minutes (less volatile)
    def get_crypto_info(
        self,
        crypto_id: str,
        base_url: str,
    ) -> dict:
        """Fetches and returns latest crypto information with caching."""
        
        try:
            url = f"{base_url}/coins/{crypto_id}"
            logger.debug(f"🌐 Fetching crypto info: {crypto_id}")
            
            time.sleep(0.1)  # Rate limit (only when not cached)
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result = {
                    'name': data.get('name', 'N/A'),
                    'symbol': data.get('symbol', 'N/A').upper(),
                    'current_price': data.get('market_data', {}).get('current_price', {}).get('usd', 0),
                    'market_cap': data.get('market_data', {}).get('market_cap', {}).get('usd', 0),
                    'total_volume': data.get('market_data', {}).get('total_volume', {}).get('usd', 0),
                    'price_change_24h': data.get('market_data', {}).get('price_change_percentage_24h', 0),
                }
                logger.info(f"✅ Fetched info for {result['name']} ({result['symbol']})")
                return result
            else:
                logger.warning(f"⚠️  API response {response.status_code} for {crypto_id}")
                
        except Exception as e:
            logger.error(f"❌ Error fetching crypto info for {crypto_id}: {e}")
            
        return {'name': 'N/A', 'symbol': 'N/A', 'current_price': 0}

    def get_crypto_market_data(
        self,
        crypto_id: str,
        base_url: str,
        save_path: Optional[str] = None,
    ) -> DataFrame:
        """Fetches and returns crypto market data as a DataFrame."""
        
        info = self.get_crypto_info(crypto_id, base_url)
        market_data = {
            "Name": info.get("name", "N/A"),
            "Symbol": info.get("symbol", "N/A"),
            "Current Price (USD)": info.get("current_price", "N/A"),
            "Market Cap (USD)": info.get("market_cap", "N/A"),
            "24h Volume (USD)": info.get("total_volume", "N/A"),
            "24h Price Change (%)": info.get("price_change_24h", "N/A"),
        }
        market_data_df = DataFrame([market_data])
        if save_path:
            market_data_df.to_csv(save_path)
            print(f"Crypto market data for {info.get('symbol', 'N/A')} saved to {save_path}")
        return market_data_df

    def get_crypto_metrics(
        self,
        crypto_id: str,
        base_url: str,
        save_path: Optional[str] = None,
    ) -> DataFrame:
        """Fetches and returns crypto-specific metrics (on-chain data placeholder)."""
        
        # TODO: Integrate real on-chain metrics APIs (e.g., Glassnode, IntoTheBlock)
        # For now, return placeholder data structure
        
        metrics_data = {
            "Active Addresses (24h)": "TODO: Connect to on-chain API",
            "Network Hash Rate": "TODO: Connect to on-chain API", 
            "Transaction Volume (24h)": "TODO: Connect to on-chain API",
            "Developer Activity": "TODO: Connect to GitHub API",
            "Social Sentiment Score": "TODO: Connect to social APIs",
        }
        metrics_df = DataFrame([metrics_data])
        if save_path:
            metrics_df.to_csv(save_path)
            print(f"Crypto metrics for {crypto_id} saved to {save_path}")
        return metrics_df 