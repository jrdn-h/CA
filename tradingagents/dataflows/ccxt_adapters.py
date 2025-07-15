"""CCXT adapters for exchange-specific OHLCV and order book depth data."""

import ccxt
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
import time
from functools import wraps

from .crypto_cache import cache_crypto_request, get_cache_manager
from .utils import decorate_all_methods

logger = logging.getLogger(__name__)


class ExchangeConfig:
    """Configuration for supported exchanges with their capabilities."""
    
    SUPPORTED_EXCHANGES = {
        'binance': {
            'class': ccxt.binance,
            'has_ohlcv': True,
            'has_order_book': True,
            'rate_limit': 1200,  # requests per minute
            'sandbox': False,
            'fees': 0.001  # 0.1% trading fee
        },
        'coinbase': {
            'class': ccxt.coinbase,
            'has_ohlcv': True,
            'has_order_book': True,
            'rate_limit': 600,
            'sandbox': True,
            'fees': 0.005  # 0.5% trading fee
        },
        'kraken': {
            'class': ccxt.kraken,
            'has_ohlcv': True,
            'has_order_book': True,
            'rate_limit': 60,
            'sandbox': False,
            'fees': 0.0026  # 0.26% trading fee
        },
        'okx': {
            'class': ccxt.okx,
            'has_ohlcv': True,
            'has_order_book': True,
            'rate_limit': 1200,
            'sandbox': True,
            'fees': 0.001  # 0.1% trading fee
        },
        'huobi': {
            'class': ccxt.huobi,
            'has_ohlcv': True,
            'has_order_book': True,
            'rate_limit': 600,
            'sandbox': False,
            'fees': 0.002  # 0.2% trading fee
        }
    }

    @classmethod
    def get_exchange_info(cls, exchange_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration info for a specific exchange."""
        return cls.SUPPORTED_EXCHANGES.get(exchange_name.lower())

    @classmethod
    def list_exchanges(cls) -> List[str]:
        """List all supported exchange names."""
        return list(cls.SUPPORTED_EXCHANGES.keys())


def init_exchange_client(func):
    """Decorator to initialize exchange client and handle rate limiting."""
    
    @wraps(func)
    def wrapper(self, exchange_name: str, symbol: str, *args, **kwargs):
        exchange_config = ExchangeConfig.get_exchange_info(exchange_name)
        if not exchange_config:
            raise ValueError(f"Unsupported exchange: {exchange_name}")
        
        # Get or create exchange client
        client = self._get_exchange_client(exchange_name, exchange_config)
        
        # Rate limiting
        rate_limit = exchange_config['rate_limit']
        min_interval = 60.0 / rate_limit  # seconds between requests
        
        current_time = time.time()
        last_request_key = f"last_request_{exchange_name}"
        last_request = getattr(self, last_request_key, 0)
        
        if current_time - last_request < min_interval:
            sleep_time = min_interval - (current_time - last_request)
            time.sleep(sleep_time)
        
        setattr(self, last_request_key, time.time())
        
        return func(self, client, symbol, *args, **kwargs)
    
    return wrapper


class CCXTAdapters:
    """CCXT adapters for exchange-specific cryptocurrency data."""
    
    def __init__(self):
        """Initialize CCXT adapters with exchange clients cache."""
        self._exchange_clients = {}
        self.cache_manager = get_cache_manager()
        logger.info("🏦 CCXTAdapters initialized")
    
    def _get_exchange_client(self, exchange_name: str, config: Dict[str, Any]) -> ccxt.Exchange:
        """Get or create exchange client with proper configuration."""
        if exchange_name not in self._exchange_clients:
            exchange_class = config['class']
            
            # Initialize with sandbox mode if available
            params = {
                'rateLimit': 60000 / config['rate_limit'],  # Convert to milliseconds
                'enableRateLimit': True,
            }
            
            if config.get('sandbox'):
                params['sandbox'] = True
            
            client = exchange_class(params)
            
            # Test connection
            try:
                client.load_markets()
                logger.info(f"✅ Connected to {exchange_name} exchange")
            except Exception as e:
                logger.warning(f"⚠️  Connection warning for {exchange_name}: {e}")
            
            self._exchange_clients[exchange_name] = client
        
        return self._exchange_clients[exchange_name]

    @cache_crypto_request("ccxt_ohlcv", ttl=30)
    @init_exchange_client
    def fetch_ohlcv(self, client: ccxt.Exchange, symbol: str, 
                   timeframe: str = '1h', limit: int = 100) -> pd.DataFrame:
        """Fetch OHLCV data from specific exchange.
        
        Args:
            client: CCXT exchange client
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            timeframe: Candlestick timeframe ('1m', '5m', '1h', '1d', etc.)
            limit: Number of candlesticks to fetch
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Ensure symbol is available on the exchange
            if symbol not in client.symbols:
                # Try common variations
                variations = [
                    symbol.replace('/', 'USDT').replace('USDT', '/USDT'),
                    symbol.replace('/', 'USD').replace('USD', '/USD'),
                    symbol.replace('-', '/'),
                ]
                for variation in variations:
                    if variation in client.symbols:
                        symbol = variation
                        break
                else:
                    available_symbols = [s for s in client.symbols if symbol.split('/')[0] in s]
                    if available_symbols:
                        symbol = available_symbols[0]
                        logger.info(f"Using available symbol: {symbol}")
                    else:
                        raise ValueError(f"Symbol {symbol} not found on {client.name}")
            
            # Fetch OHLCV data
            ohlcv_data = client.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Add exchange info
            df['exchange'] = client.name
            df['symbol'] = symbol
            df['timeframe'] = timeframe
            
            logger.info(f"📊 Fetched {len(df)} OHLCV candles for {symbol} from {client.name}")
            return df
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch OHLCV from {client.name}: {e}")
            raise

    @cache_crypto_request("ccxt_orderbook", ttl=10)
    @init_exchange_client
    def fetch_order_book(self, client: ccxt.Exchange, symbol: str, 
                        limit: int = 50) -> Dict[str, Any]:
        """Fetch order book depth from specific exchange.
        
        Args:
            client: CCXT exchange client
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            limit: Number of order book levels to fetch
            
        Returns:
            Dictionary with order book data and analysis
        """
        try:
            # Ensure symbol is available
            if symbol not in client.symbols:
                # Try common variations (same logic as OHLCV)
                variations = [
                    symbol.replace('/', 'USDT').replace('USDT', '/USDT'),
                    symbol.replace('/', 'USD').replace('USD', '/USD'),
                    symbol.replace('-', '/'),
                ]
                for variation in variations:
                    if variation in client.symbols:
                        symbol = variation
                        break
                else:
                    available_symbols = [s for s in client.symbols if symbol.split('/')[0] in s]
                    if available_symbols:
                        symbol = available_symbols[0]
                    else:
                        raise ValueError(f"Symbol {symbol} not found on {client.name}")
            
            # Fetch order book
            order_book = client.fetch_order_book(symbol, limit)
            
            # Calculate order book analytics
            bids = order_book['bids']
            asks = order_book['asks']
            
            if not bids or not asks:
                raise ValueError("Empty order book")
            
            # Best bid/ask
            best_bid = bids[0][0] if bids else 0
            best_ask = asks[0][0] if asks else 0
            spread = best_ask - best_bid if best_bid and best_ask else 0
            spread_pct = (spread / best_ask * 100) if best_ask else 0
            
            # Volume analysis
            bid_volume = sum([level[1] for level in bids[:10]])  # Top 10 levels
            ask_volume = sum([level[1] for level in asks[:10]])
            volume_imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume) if (bid_volume + ask_volume) > 0 else 0
            
            # Depth analysis
            bid_depth = sum([level[0] * level[1] for level in bids[:5]])  # Value in quote currency
            ask_depth = sum([level[0] * level[1] for level in asks[:5]])
            
            result = {
                'exchange': client.name,
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'bids': bids[:limit],
                'asks': asks[:limit],
                'spread': {
                    'absolute': spread,
                    'percentage': spread_pct,
                    'best_bid': best_bid,
                    'best_ask': best_ask
                },
                'volume_analysis': {
                    'bid_volume_top10': bid_volume,
                    'ask_volume_top10': ask_volume,
                    'volume_imbalance': volume_imbalance,  # Positive = more bids, Negative = more asks
                    'imbalance_signal': 'BULLISH' if volume_imbalance > 0.1 else 'BEARISH' if volume_imbalance < -0.1 else 'NEUTRAL'
                },
                'depth_analysis': {
                    'bid_depth_top5': bid_depth,
                    'ask_depth_top5': ask_depth,
                    'total_depth': bid_depth + ask_depth,
                    'depth_ratio': bid_depth / ask_depth if ask_depth > 0 else 0
                },
                'market_quality': {
                    'spread_category': 'TIGHT' if spread_pct < 0.05 else 'NORMAL' if spread_pct < 0.1 else 'WIDE',
                    'liquidity_score': min(100, (bid_depth + ask_depth) / 10000),  # Normalized liquidity score
                    'order_book_levels': len(bids) + len(asks)
                }
            }
            
            logger.info(f"📚 Fetched order book for {symbol} from {client.name} - Spread: {spread_pct:.3f}%")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch order book from {client.name}: {e}")
            raise

    def get_exchange_comparison(self, symbol: str, exchanges: List[str] = None, 
                              timeframe: str = '1h') -> Dict[str, Any]:
        """Compare data across multiple exchanges for arbitrage opportunities.
        
        Args:
            symbol: Trading pair symbol
            exchanges: List of exchange names to compare (default: all supported)
            timeframe: Timeframe for OHLCV comparison
            
        Returns:
            Comparison data across exchanges
        """
        if exchanges is None:
            exchanges = ['binance', 'coinbase', 'kraken']
        
        comparison = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'exchanges': {},
            'arbitrage_opportunities': [],
            'best_liquidity': None,
            'tightest_spread': None
        }
        
        prices = {}
        spreads = {}
        liquidities = {}
        
        for exchange_name in exchanges:
            try:
                # Get order book for current price and spread
                order_book = self.fetch_order_book(exchange_name, symbol, limit=10)
                
                current_price = (order_book['spread']['best_bid'] + order_book['spread']['best_ask']) / 2
                spread_pct = order_book['spread']['percentage']
                liquidity = order_book['depth_analysis']['total_depth']
                
                prices[exchange_name] = current_price
                spreads[exchange_name] = spread_pct
                liquidities[exchange_name] = liquidity
                
                comparison['exchanges'][exchange_name] = {
                    'price': current_price,
                    'spread_pct': spread_pct,
                    'liquidity': liquidity,
                    'volume_imbalance': order_book['volume_analysis']['volume_imbalance'],
                    'market_quality': order_book['market_quality']
                }
                
            except Exception as e:
                logger.warning(f"⚠️  Failed to get data from {exchange_name}: {e}")
                comparison['exchanges'][exchange_name] = {'error': str(e)}
        
        # Find arbitrage opportunities
        if len(prices) >= 2:
            price_list = list(prices.items())
            for i in range(len(price_list)):
                for j in range(i + 1, len(price_list)):
                    exchange1, price1 = price_list[i]
                    exchange2, price2 = price_list[j]
                    
                    price_diff_pct = abs(price1 - price2) / min(price1, price2) * 100
                    
                    if price_diff_pct > 0.1:  # Significant price difference
                        comparison['arbitrage_opportunities'].append({
                            'buy_exchange': exchange1 if price1 < price2 else exchange2,
                            'sell_exchange': exchange2 if price1 < price2 else exchange1,
                            'price_difference_pct': price_diff_pct,
                            'potential_profit': price_diff_pct - 0.2  # Minus estimated trading fees
                        })
        
        # Find best liquidity and tightest spread
        if liquidities:
            comparison['best_liquidity'] = max(liquidities.items(), key=lambda x: x[1])
        if spreads:
            comparison['tightest_spread'] = min(spreads.items(), key=lambda x: x[1])
        
        return comparison

    def get_supported_exchanges(self) -> List[Dict[str, Any]]:
        """Get list of supported exchanges with their capabilities."""
        return [
            {
                'name': name,
                'has_ohlcv': config['has_ohlcv'],
                'has_order_book': config['has_order_book'],
                'rate_limit_per_minute': config['rate_limit'],
                'trading_fees': config['fees'],
                'sandbox_available': config.get('sandbox', False)
            }
            for name, config in ExchangeConfig.SUPPORTED_EXCHANGES.items()
        ] 