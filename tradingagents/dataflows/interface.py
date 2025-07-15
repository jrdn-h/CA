from typing import Annotated, Dict
from .reddit_utils import fetch_top_from_category
from .yfin_utils import *
from .stockstats_utils import *
from .googlenews_utils import *
from .finnhub_utils import get_data_in_range
from .crypto_utils import CryptoUtils
from .ccxt_adapters import CCXTAdapters
from .onchain_loader import get_onchain_loader
from .metric_registry import get_metric_registry
from dateutil.relativedelta import relativedelta
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import os
import pandas as pd
from tqdm import tqdm
import yfinance as yf
from openai import OpenAI
from .config import get_config, set_config, DATA_DIR


def get_finnhub_news(
    ticker: Annotated[
        str,
        "Search query of a company's, e.g. 'AAPL, TSM, etc.",
    ],
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
):
    """
    Retrieve news about a company within a time frame

    Args
        ticker (str): ticker for the company you are interested in
        start_date (str): Start date in yyyy-mm-dd format
        end_date (str): End date in yyyy-mm-dd format
    Returns
        str: dataframe containing the news of the company in the time frame

    """

    start_date = datetime.strptime(curr_date, "%Y-%m-%d")
    before = start_date - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    result = get_data_in_range(ticker, before, curr_date, "news_data", DATA_DIR)

    if len(result) == 0:
        return ""

    combined_result = ""
    for day, data in result.items():
        if len(data) == 0:
            continue
        for entry in data:
            current_news = (
                "### " + entry["headline"] + f" ({day})" + "\n" + entry["summary"]
            )
            combined_result += current_news + "\n\n"

    return f"## {ticker} News, from {before} to {curr_date}:\n" + str(combined_result)


def get_crypto_data_online(
    symbol: Annotated[str, "crypto symbol like BTC, ETH, BTC-USD"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve crypto price data from CoinGecko API.
    
    Args:
        symbol (str): Crypto symbol like BTC, ETH, BTC-USD
        start_date (str): Start date in yyyy-mm-dd format
        end_date (str): End date in yyyy-mm-dd format
    Returns:
        str: Formatted DataFrame containing crypto price data
    """
    config = get_config()
    
    # Check if crypto mode is enabled
    if not config.get("use_crypto", False):
        return "Crypto mode is not enabled in configuration."
    
    try:
        crypto_utils = CryptoUtils()
        crypto_data = crypto_utils.get_crypto_data(symbol, start_date, end_date)
        
        if crypto_data.empty:
            return f"No crypto data found for {symbol} between {start_date} and {end_date}"
        
        return f"## {symbol} Crypto Price Data from {start_date} to {end_date}:\n{crypto_data.to_string()}"
        
    except Exception as e:
        return f"Error fetching crypto data for {symbol}: {str(e)}"


def get_crypto_info_online(
    symbol: Annotated[str, "crypto symbol like BTC, ETH, BTC-USD"],
) -> str:
    """
    Retrieve current crypto market information from CoinGecko API.
    
    Args:
        symbol (str): Crypto symbol like BTC, ETH, BTC-USD
    Returns:
        str: Formatted crypto market information
    """
    config = get_config()
    
    # Check if crypto mode is enabled
    if not config.get("use_crypto", False):
        return "Crypto mode is not enabled in configuration."
    
    try:
        crypto_utils = CryptoUtils()
        crypto_info = crypto_utils.get_crypto_info(symbol)
        
        info_text = f"## {symbol} Market Information:\n"
        info_text += f"Name: {crypto_info.get('name', 'N/A')}\n"
        info_text += f"Symbol: {crypto_info.get('symbol', 'N/A')}\n"
        info_text += f"Current Price: ${crypto_info.get('current_price', 0):,.2f}\n"
        info_text += f"Market Cap: ${crypto_info.get('market_cap', 0):,.0f}\n"
        info_text += f"24h Volume: ${crypto_info.get('total_volume', 0):,.0f}\n"
        info_text += f"24h Price Change: {crypto_info.get('price_change_24h', 0):+.2f}%\n"
        
        return info_text
        
    except Exception as e:
        return f"Error fetching crypto info for {symbol}: {str(e)}"


def get_exchange_ohlcv_data(
    exchange: Annotated[str, "Exchange name like 'binance', 'kraken', 'coinbase'"],
    symbol: Annotated[str, "Trading pair symbol like 'BTC/USDT', 'ETH/USD'"],
    timeframe: Annotated[str, "Timeframe like '1h', '4h', '1d'"] = '1h',
    limit: Annotated[int, "Number of candles to fetch"] = 100,
) -> str:
    """
    Fetch OHLCV data from a specific cryptocurrency exchange using CCXT.
    
    Args:
        exchange (str): Exchange name (binance, kraken, coinbase, okx, huobi)
        symbol (str): Trading pair symbol (e.g., 'BTC/USDT', 'ETH/USD')
        timeframe (str): Candlestick timeframe ('1m', '5m', '1h', '4h', '1d')
        limit (int): Number of candlesticks to fetch
    Returns:
        str: Formatted DataFrame with OHLCV data
    """
    config = get_config()
    
    # Check if crypto mode is enabled
    if not config.get("use_crypto", False):
        return "Crypto mode is not enabled in configuration."
    
    try:
        ccxt_adapters = CCXTAdapters()
        df = ccxt_adapters.fetch_ohlcv(exchange, symbol, timeframe=timeframe, limit=limit)
        
        if df.empty:
            return f"No OHLCV data found for {symbol} on {exchange}"
        
        # Add some basic analytics
        latest_price = df['close'].iloc[-1]
        price_change = df['close'].iloc[-1] - df['close'].iloc[-2] if len(df) > 1 else 0
        price_change_pct = (price_change / df['close'].iloc[-2] * 100) if len(df) > 1 and df['close'].iloc[-2] != 0 else 0
        avg_volume = df['volume'].tail(10).mean()
        
        result = f"## {symbol} OHLCV Data from {exchange.upper()} ({timeframe} timeframe):\n"
        result += f"Latest Price: ${latest_price:,.2f}\n"
        result += f"Price Change: {price_change:+.2f} ({price_change_pct:+.2f}%)\n"
        result += f"Average Volume (10 periods): {avg_volume:,.2f}\n"
        result += f"Data Points: {len(df)} candles\n\n"
        result += df.tail(20).to_string()  # Show last 20 candles
        
        return result
        
    except Exception as e:
        return f"Error fetching OHLCV data from {exchange}: {str(e)}"


def get_exchange_order_book(
    exchange: Annotated[str, "Exchange name like 'binance', 'kraken', 'coinbase'"],
    symbol: Annotated[str, "Trading pair symbol like 'BTC/USDT', 'ETH/USD'"],
    limit: Annotated[int, "Number of order book levels to fetch"] = 20,
) -> str:
    """
    Fetch order book depth from a specific cryptocurrency exchange using CCXT.
    
    Args:
        exchange (str): Exchange name (binance, kraken, coinbase, okx, huobi)
        symbol (str): Trading pair symbol (e.g., 'BTC/USDT', 'ETH/USD')
        limit (int): Number of order book levels to fetch
    Returns:
        str: Formatted order book data with analysis
    """
    config = get_config()
    
    # Check if crypto mode is enabled
    if not config.get("use_crypto", False):
        return "Crypto mode is not enabled in configuration."
    
    try:
        ccxt_adapters = CCXTAdapters()
        order_book = ccxt_adapters.fetch_order_book(exchange, symbol, limit=limit)
        
        # Format the analysis
        spread = order_book['spread']
        volume = order_book['volume_analysis']
        depth = order_book['depth_analysis']
        quality = order_book['market_quality']
        
        result = f"## {symbol} Order Book Analysis from {exchange.upper()}:\n\n"
        
        result += "### Spread Analysis:\n"
        result += f"Best Bid: ${spread['best_bid']:,.2f}\n"
        result += f"Best Ask: ${spread['best_ask']:,.2f}\n"
        result += f"Spread: ${spread['absolute']:.2f} ({spread['percentage']:.4f}%)\n\n"
        
        result += "### Volume Dynamics:\n"
        result += f"Bid Volume (Top 10): {volume['bid_volume_top10']:,.2f}\n"
        result += f"Ask Volume (Top 10): {volume['ask_volume_top10']:,.2f}\n"
        result += f"Volume Imbalance: {volume['volume_imbalance']:+.3f}\n"
        result += f"Market Signal: {volume['imbalance_signal']}\n\n"
        
        result += "### Market Depth:\n"
        result += f"Bid Depth (Top 5): ${depth['bid_depth_top5']:,.0f}\n"
        result += f"Ask Depth (Top 5): ${depth['ask_depth_top5']:,.0f}\n"
        result += f"Total Depth: ${depth['total_depth']:,.0f}\n\n"
        
        result += "### Market Quality:\n"
        result += f"Spread Category: {quality['spread_category']}\n"
        result += f"Liquidity Score: {quality['liquidity_score']:.1f}/100\n"
        result += f"Order Book Levels: {quality['order_book_levels']}\n\n"
        
        # Add top 5 bids and asks
        result += "### Top Order Book Levels:\n"
        result += "BIDS:\n"
        for i, (price, volume) in enumerate(order_book['bids'][:5], 1):
            result += f"  {i}. ${price:,.2f} - {volume:.2f}\n"
        
        result += "\nASKS:\n"
        for i, (price, volume) in enumerate(order_book['asks'][:5], 1):
            result += f"  {i}. ${price:,.2f} - {volume:.2f}\n"
        
        return result
        
    except Exception as e:
        return f"Error fetching order book from {exchange}: {str(e)}"


def compare_crypto_exchanges(
    symbol: Annotated[str, "Trading pair symbol like 'BTC/USDT', 'ETH/USD'"],
    exchanges: Annotated[str, "Comma-separated exchange names"] = "binance,kraken,coinbase",
) -> str:
    """
    Compare cryptocurrency prices and liquidity across multiple exchanges for arbitrage opportunities.
    
    Args:
        symbol (str): Trading pair symbol (e.g., 'BTC/USDT', 'ETH/USD')
        exchanges (str): Comma-separated list of exchange names
    Returns:
        str: Exchange comparison with arbitrage opportunities
    """
    config = get_config()
    
    # Check if crypto mode is enabled
    if not config.get("use_crypto", False):
        return "Crypto mode is not enabled in configuration."
    
    try:
        exchange_list = [ex.strip() for ex in exchanges.split(',')]
        ccxt_adapters = CCXTAdapters()
        comparison = ccxt_adapters.get_exchange_comparison(symbol, exchanges=exchange_list)
        
        result = f"## Cross-Exchange Analysis for {symbol}:\n\n"
        
        # Exchange data
        result += "### Exchange Comparison:\n"
        exchanges_data = comparison['exchanges']
        successful_exchanges = []
        
        for exchange_name, data in exchanges_data.items():
            if 'error' not in data:
                successful_exchanges.append(exchange_name)
                result += f"**{exchange_name.upper()}:**\n"
                result += f"  Price: ${data['price']:,.2f}\n"
                result += f"  Spread: {data['spread_pct']:.3f}%\n"
                result += f"  Liquidity: ${data['liquidity']:,.0f}\n"
                result += f"  Volume Signal: {data['volume_imbalance']:+.3f}\n"
                result += f"  Quality: {data['market_quality']['spread_category']}\n\n"
            else:
                result += f"**{exchange_name.upper()}:** ❌ {data['error']}\n\n"
        
        # Arbitrage opportunities
        arbitrage_ops = comparison.get('arbitrage_opportunities', [])
        if arbitrage_ops:
            result += "### 💰 Arbitrage Opportunities:\n"
            for i, op in enumerate(arbitrage_ops, 1):
                profit_indicator = "🟢" if op['potential_profit'] > 0.5 else "🟡" if op['potential_profit'] > 0.1 else "🔴"
                result += f"{profit_indicator} **Opportunity #{i}:**\n"
                result += f"  Buy on: {op['buy_exchange'].upper()}\n"
                result += f"  Sell on: {op['sell_exchange'].upper()}\n"
                result += f"  Price Difference: {op['price_difference_pct']:.2f}%\n"
                result += f"  Estimated Profit: {op['potential_profit']:.2f}%\n\n"
        else:
            result += "### 📊 Arbitrage Analysis:\n"
            if len(successful_exchanges) >= 2:
                result += "No significant arbitrage opportunities found. Market prices are well-aligned.\n\n"
            else:
                result += "Insufficient exchange data for arbitrage analysis.\n\n"
        
        # Best venues
        if comparison.get('best_liquidity'):
            best_liquidity = comparison['best_liquidity']
            result += f"**🏆 Best Liquidity:** {best_liquidity[0].upper()} (${best_liquidity[1]:,.0f})\n"
        
        if comparison.get('tightest_spread'):
            tightest_spread = comparison['tightest_spread']
            result += f"**⚡ Tightest Spread:** {tightest_spread[0].upper()} ({tightest_spread[1]:.3f}%)\n"
        
        return result
        
    except Exception as e:
        return f"Error comparing exchanges: {str(e)}"


def get_supported_crypto_exchanges() -> str:
    """
    Get a list of supported cryptocurrency exchanges and their capabilities.
    
    Returns:
        str: Formatted list of supported exchanges with capabilities
    """
    config = get_config()
    
    # Check if crypto mode is enabled
    if not config.get("use_crypto", False):
        return "Crypto mode is not enabled in configuration."
    
    try:
        ccxt_adapters = CCXTAdapters()
        exchanges = ccxt_adapters.get_supported_exchanges()
        
        result = "## Supported Cryptocurrency Exchanges:\n\n"
        
        for exchange in exchanges:
            sandbox_status = "🧪 Sandbox Available" if exchange['sandbox_available'] else "🔴 Live Only"
            
            result += f"### 🏦 {exchange['name'].upper()}\n"
            result += f"- 📈 OHLCV Data: {'✅' if exchange['has_ohlcv'] else '❌'}\n"
            result += f"- 📚 Order Book: {'✅' if exchange['has_order_book'] else '❌'}\n"
            result += f"- ⚡ Rate Limit: {exchange['rate_limit_per_minute']:,} requests/minute\n"
            result += f"- 💰 Trading Fees: {exchange['trading_fees']*100:.2f}%\n"
            result += f"- 🛡️  Testing: {sandbox_status}\n\n"
        
        result += f"**Total Exchanges:** {len(exchanges)}\n\n"
        result += "**Usage Examples:**\n"
        result += "- `get_exchange_ohlcv_data('binance', 'BTC/USDT', '1h', 50)`\n"
        result += "- `get_exchange_order_book('kraken', 'ETH/USD', 20)`\n"
        result += "- `compare_crypto_exchanges('BTC/USDT', 'binance,kraken,coinbase')`\n"
        
        return result
        
    except Exception as e:
        return f"Error getting supported exchanges: {str(e)}"


def get_onchain_network_health(
    symbol: Annotated[str, "crypto symbol like BTC, ETH"],
) -> str:
    """
    Retrieve comprehensive network health metrics for a cryptocurrency.
    
    Args:
        symbol (str): Crypto symbol like BTC, ETH
    Returns:
        str: Formatted network health analysis
    """
    config = get_config()
    
    # Check if crypto mode is enabled
    if not config.get("use_crypto", False):
        return "Crypto mode is not enabled in configuration."
    
    try:
        onchain_loader = get_onchain_loader()
        health_data = onchain_loader.get_network_health(symbol)
        
        result = f"## {symbol} Network Health Analysis:\n\n"
        result += f"**Health Score:** {health_data['health_score']}/100 ({health_data['status']})\n\n"
        
        result += "### Network Metrics:\n"
        metrics = health_data['metrics']
        result += f"- Active Addresses (24h): {metrics.get('active_addresses', 'N/A'):,}\n"
        result += f"- Hash Rate: {metrics.get('hash_rate', 'N/A')}\n"
        result += f"- Transaction Count (24h): {metrics.get('transactions_24h', 'N/A'):,}\n"
        result += f"- Average Fee: ${metrics.get('avg_fee_usd', 'N/A'):.4f}\n\n"
        
        result += f"**Analysis:** {health_data['analysis']}\n"
        
        return result
        
    except Exception as e:
        return f"Error fetching network health for {symbol}: {str(e)}"


def get_onchain_market_indicators(
    symbol: Annotated[str, "crypto symbol like BTC, ETH"],
) -> str:
    """
    Retrieve on-chain market indicators for a cryptocurrency.
    
    Args:
        symbol (str): Crypto symbol like BTC, ETH
    Returns:
        str: Formatted market indicators
    """
    config = get_config()
    
    # Check if crypto mode is enabled
    if not config.get("use_crypto", False):
        return "Crypto mode is not enabled in configuration."
    
    try:
        onchain_loader = get_onchain_loader()
        indicators = onchain_loader.get_market_indicators(symbol)
        
        result = f"## {symbol} On-Chain Market Indicators:\n\n"
        
        result += "### Exchange Flows:\n"
        exchange_flows = indicators.get('exchange_flows', {})
        result += f"- Net Flow: {exchange_flows.get('net_flow', 'N/A')}\n"
        result += f"- Signal: {exchange_flows.get('signal', 'N/A')}\n"
        result += f"- Trend: {exchange_flows.get('trend', 'N/A')}\n\n"
        
        result += "### Whale Activity:\n"
        whale_activity = indicators.get('whale_activity', {})
        result += f"- Large Transactions (24h): {whale_activity.get('large_transactions_24h', 'N/A')}\n"
        result += f"- Whale Accumulation: {whale_activity.get('whale_accumulation', 'N/A')}\n"
        result += f"- Activity Level: {whale_activity.get('activity_level', 'N/A')}\n\n"
        
        result += "### HODL Metrics:\n"
        hodl_metrics = indicators.get('hodl_metrics', {})
        result += f"- Long-term Holders: {hodl_metrics.get('long_term_holders_pct', 'N/A')}%\n"
        result += f"- Supply Distribution: {hodl_metrics.get('supply_distribution', 'N/A')}\n\n"
        
        result += f"**Investment Implications:** {indicators.get('investment_implications', 'N/A')}\n"
        
        return result
        
    except Exception as e:
        return f"Error fetching market indicators for {symbol}: {str(e)}"


def get_onchain_comprehensive_analysis(
    symbol: Annotated[str, "crypto symbol like BTC, ETH"],
) -> str:
    """
    Retrieve comprehensive on-chain analysis for a cryptocurrency.
    
    Args:
        symbol (str): Crypto symbol like BTC, ETH
    Returns:
        str: Comprehensive on-chain analysis
    """
    config = get_config()
    
    # Check if crypto mode is enabled
    if not config.get("use_crypto", False):
        return "Crypto mode is not enabled in configuration."
    
    try:
        onchain_loader = get_onchain_loader()
        analysis = onchain_loader.get_comprehensive_analysis(symbol)
        
        result = f"## {symbol} Comprehensive On-Chain Analysis:\n\n"
        
        # Network Health Summary
        network_health = analysis.get('network_health', {})
        result += f"**Network Health:** {network_health.get('status', 'N/A')} "
        result += f"(Score: {network_health.get('score', 'N/A')}/100)\n\n"
        
        # Market Indicators Summary
        market_indicators = analysis.get('market_indicators', {})
        result += "### Key Market Signals:\n"
        exchange_flows = market_indicators.get('exchange_flows', {})
        result += f"- Exchange Flow Signal: {exchange_flows.get('signal', 'N/A')}\n"
        
        whale_activity = market_indicators.get('whale_activity', {})
        result += f"- Whale Activity: {whale_activity.get('activity_level', 'N/A')}\n"
        
        hodl_metrics = market_indicators.get('hodl_metrics', {})
        result += f"- Long-term Holders: {hodl_metrics.get('long_term_holders_pct', 'N/A')}%\n\n"
        
        # AI Insights
        ai_insights = analysis.get('ai_insights', {})
        result += "### AI-Powered Investment Analysis:\n"
        result += f"**Confidence Score:** {ai_insights.get('confidence', 'N/A')}/100\n\n"
        result += f"**Investment Thesis:**\n{ai_insights.get('thesis', 'N/A')}\n\n"
        result += f"**Key Risks:** {ai_insights.get('risks', 'N/A')}\n\n"
        result += f"**Opportunities:** {ai_insights.get('opportunities', 'N/A')}\n\n"
        
        # Summary metrics
        summary = analysis.get('summary', {})
        result += "### Summary Metrics:\n"
        result += f"- Overall Sentiment: {summary.get('sentiment', 'N/A')}\n"
        result += f"- Network Adoption: {summary.get('adoption_trend', 'N/A')}\n"
        result += f"- Macro Trend: {summary.get('macro_trend', 'N/A')}\n"
        
        return result
        
    except Exception as e:
        return f"Error fetching comprehensive analysis for {symbol}: {str(e)}"


def get_metric_registry_data(
    metric: Annotated[str, "metric name like 'active_addresses', 'whale_activity'"],
    symbol: Annotated[str, "crypto symbol like BTC, ETH"],
) -> str:
    """
    Retrieve specific on-chain metrics using the intelligent fallback system.
    
    Args:
        metric (str): Specific metric name
        symbol (str): Crypto symbol like BTC, ETH
    Returns:
        str: Formatted metric data with provider information
    """
    config = get_config()
    
    # Check if crypto mode is enabled
    if not config.get("use_crypto", False):
        return "Crypto mode is not enabled in configuration."
    
    try:
        registry = get_metric_registry()
        data = registry.get_metric(metric, symbol)
        
        if data is None:
            return f"No data available for metric '{metric}' and symbol '{symbol}'"
        
        result = f"## {metric.replace('_', ' ').title()} for {symbol}:\n\n"
        
        # Get provider status to show which provider was used
        provider_status = registry.get_provider_status()
        active_providers = [p for p, status in provider_status['providers'].items() 
                          if status['healthy']]
        
        if isinstance(data, dict):
            if 'value' in data:
                result += f"**Value:** {data['value']}\n"
            if 'timestamp' in data:
                result += f"**Timestamp:** {data['timestamp']}\n"
            if 'provider' in data:
                result += f"**Data Provider:** {data['provider']}\n"
            if 'confidence' in data:
                result += f"**Confidence:** {data['confidence']}/100\n"
            
            # Add other data fields
            for key, value in data.items():
                if key not in ['value', 'timestamp', 'provider', 'confidence']:
                    result += f"**{key.replace('_', ' ').title()}:** {value}\n"
        else:
            result += f"**Value:** {data}\n"
        
        result += f"\n**System Status:** {len(active_providers)} providers healthy\n"
        result += f"**Data Availability:** {provider_status['availability']}%\n"
        
        return result
        
    except Exception as e:
        return f"Error fetching metric '{metric}' for {symbol}: {str(e)}"



def get_finnhub_company_insider_sentiment(
    ticker: Annotated[str, "ticker symbol for the company"],
    curr_date: Annotated[
        str,
        "current date of you are trading at, yyyy-mm-dd",
    ],
    look_back_days: Annotated[int, "number of days to look back"],
):
    """
    Retrieve insider sentiment about a company (retrieved from public SEC information) for the past 15 days
    Args:
        ticker (str): ticker symbol of the company
        curr_date (str): current date you are trading on, yyyy-mm-dd
    Returns:
        str: a report of the sentiment in the past 15 days starting at curr_date
    """

    date_obj = datetime.strptime(curr_date, "%Y-%m-%d")
    before = date_obj - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    data = get_data_in_range(ticker, before, curr_date, "insider_senti", DATA_DIR)

    if len(data) == 0:
        return ""

    result_str = ""
    seen_dicts = []
    for date, senti_list in data.items():
        for entry in senti_list:
            if entry not in seen_dicts:
                result_str += f"### {entry['year']}-{entry['month']}:\nChange: {entry['change']}\nMonthly Share Purchase Ratio: {entry['mspr']}\n\n"
                seen_dicts.append(entry)

    return (
        f"## {ticker} Insider Sentiment Data for {before} to {curr_date}:\n"
        + result_str
        + "The change field refers to the net buying/selling from all insiders' transactions. The mspr field refers to monthly share purchase ratio."
    )


def get_finnhub_company_insider_transactions(
    ticker: Annotated[str, "ticker symbol"],
    curr_date: Annotated[
        str,
        "current date you are trading at, yyyy-mm-dd",
    ],
    look_back_days: Annotated[int, "how many days to look back"],
):
    """
    Retrieve insider transcaction information about a company (retrieved from public SEC information) for the past 15 days
    Args:
        ticker (str): ticker symbol of the company
        curr_date (str): current date you are trading at, yyyy-mm-dd
    Returns:
        str: a report of the company's insider transaction/trading informtaion in the past 15 days
    """

    date_obj = datetime.strptime(curr_date, "%Y-%m-%d")
    before = date_obj - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    data = get_data_in_range(ticker, before, curr_date, "insider_trans", DATA_DIR)

    if len(data) == 0:
        return ""

    result_str = ""

    seen_dicts = []
    for date, senti_list in data.items():
        for entry in senti_list:
            if entry not in seen_dicts:
                result_str += f"### Filing Date: {entry['filingDate']}, {entry['name']}:\nChange:{entry['change']}\nShares: {entry['share']}\nTransaction Price: {entry['transactionPrice']}\nTransaction Code: {entry['transactionCode']}\n\n"
                seen_dicts.append(entry)

    return (
        f"## {ticker} insider transactions from {before} to {curr_date}:\n"
        + result_str
        + "The change field reflects the variation in share count—here a negative number indicates a reduction in holdings—while share specifies the total number of shares involved. The transactionPrice denotes the per-share price at which the trade was executed, and transactionDate marks when the transaction occurred. The name field identifies the insider making the trade, and transactionCode (e.g., S for sale) clarifies the nature of the transaction. FilingDate records when the transaction was officially reported, and the unique id links to the specific SEC filing, as indicated by the source. Additionally, the symbol ties the transaction to a particular company, isDerivative flags whether the trade involves derivative securities, and currency notes the currency context of the transaction."
    )


def get_simfin_balance_sheet(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[
        str,
        "reporting frequency of the company's financial history: annual / quarterly",
    ],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
):
    data_path = os.path.join(
        DATA_DIR,
        "fundamental_data",
        "simfin_data_all",
        "balance_sheet",
        "companies",
        "us",
        f"us-balance-{freq}.csv",
    )
    df = pd.read_csv(data_path, sep=";")

    # Convert date strings to datetime objects and remove any time components
    df["Report Date"] = pd.to_datetime(df["Report Date"], utc=True).dt.normalize()
    df["Publish Date"] = pd.to_datetime(df["Publish Date"], utc=True).dt.normalize()

    # Convert the current date to datetime and normalize
    curr_date_dt = pd.to_datetime(curr_date, utc=True).normalize()

    # Filter the DataFrame for the given ticker and for reports that were published on or before the current date
    filtered_df = df[(df["Ticker"] == ticker) & (df["Publish Date"] <= curr_date_dt)]

    # Check if there are any available reports; if not, return a notification
    if filtered_df.empty:
        print("No balance sheet available before the given current date.")
        return ""

    # Get the most recent balance sheet by selecting the row with the latest Publish Date
    latest_balance_sheet = filtered_df.loc[filtered_df["Publish Date"].idxmax()]

    # drop the SimFinID column
    latest_balance_sheet = latest_balance_sheet.drop("SimFinId")

    return (
        f"## {freq} balance sheet for {ticker} released on {str(latest_balance_sheet['Publish Date'])[0:10]}: \n"
        + str(latest_balance_sheet)
        + "\n\nThis includes metadata like reporting dates and currency, share details, and a breakdown of assets, liabilities, and equity. Assets are grouped as current (liquid items like cash and receivables) and noncurrent (long-term investments and property). Liabilities are split between short-term obligations and long-term debts, while equity reflects shareholder funds such as paid-in capital and retained earnings. Together, these components ensure that total assets equal the sum of liabilities and equity."
    )


def get_simfin_cashflow(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[
        str,
        "reporting frequency of the company's financial history: annual / quarterly",
    ],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
):
    data_path = os.path.join(
        DATA_DIR,
        "fundamental_data",
        "simfin_data_all",
        "cash_flow",
        "companies",
        "us",
        f"us-cashflow-{freq}.csv",
    )
    df = pd.read_csv(data_path, sep=";")

    # Convert date strings to datetime objects and remove any time components
    df["Report Date"] = pd.to_datetime(df["Report Date"], utc=True).dt.normalize()
    df["Publish Date"] = pd.to_datetime(df["Publish Date"], utc=True).dt.normalize()

    # Convert the current date to datetime and normalize
    curr_date_dt = pd.to_datetime(curr_date, utc=True).normalize()

    # Filter the DataFrame for the given ticker and for reports that were published on or before the current date
    filtered_df = df[(df["Ticker"] == ticker) & (df["Publish Date"] <= curr_date_dt)]

    # Check if there are any available reports; if not, return a notification
    if filtered_df.empty:
        print("No cash flow statement available before the given current date.")
        return ""

    # Get the most recent cash flow statement by selecting the row with the latest Publish Date
    latest_cash_flow = filtered_df.loc[filtered_df["Publish Date"].idxmax()]

    # drop the SimFinID column
    latest_cash_flow = latest_cash_flow.drop("SimFinId")

    return (
        f"## {freq} cash flow statement for {ticker} released on {str(latest_cash_flow['Publish Date'])[0:10]}: \n"
        + str(latest_cash_flow)
        + "\n\nThis includes metadata like reporting dates and currency, share details, and a breakdown of cash movements. Operating activities show cash generated from core business operations, including net income adjustments for non-cash items and working capital changes. Investing activities cover asset acquisitions/disposals and investments. Financing activities include debt transactions, equity issuances/repurchases, and dividend payments. The net change in cash represents the overall increase or decrease in the company's cash position during the reporting period."
    )


def get_simfin_income_statements(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[
        str,
        "reporting frequency of the company's financial history: annual / quarterly",
    ],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
):
    data_path = os.path.join(
        DATA_DIR,
        "fundamental_data",
        "simfin_data_all",
        "income_statements",
        "companies",
        "us",
        f"us-income-{freq}.csv",
    )
    df = pd.read_csv(data_path, sep=";")

    # Convert date strings to datetime objects and remove any time components
    df["Report Date"] = pd.to_datetime(df["Report Date"], utc=True).dt.normalize()
    df["Publish Date"] = pd.to_datetime(df["Publish Date"], utc=True).dt.normalize()

    # Convert the current date to datetime and normalize
    curr_date_dt = pd.to_datetime(curr_date, utc=True).normalize()

    # Filter the DataFrame for the given ticker and for reports that were published on or before the current date
    filtered_df = df[(df["Ticker"] == ticker) & (df["Publish Date"] <= curr_date_dt)]

    # Check if there are any available reports; if not, return a notification
    if filtered_df.empty:
        print("No income statement available before the given current date.")
        return ""

    # Get the most recent income statement by selecting the row with the latest Publish Date
    latest_income = filtered_df.loc[filtered_df["Publish Date"].idxmax()]

    # drop the SimFinID column
    latest_income = latest_income.drop("SimFinId")

    return (
        f"## {freq} income statement for {ticker} released on {str(latest_income['Publish Date'])[0:10]}: \n"
        + str(latest_income)
        + "\n\nThis includes metadata like reporting dates and currency, share details, and a comprehensive breakdown of the company's financial performance. Starting with Revenue, it shows Cost of Revenue and resulting Gross Profit. Operating Expenses are detailed, including SG&A, R&D, and Depreciation. The statement then shows Operating Income, followed by non-operating items and Interest Expense, leading to Pretax Income. After accounting for Income Tax and any Extraordinary items, it concludes with Net Income, representing the company's bottom-line profit or loss for the period."
    )


def get_google_news(
    query: Annotated[str, "Query to search with"],
    curr_date: Annotated[str, "Curr date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    query = query.replace(" ", "+")

    start_date = datetime.strptime(curr_date, "%Y-%m-%d")
    before = start_date - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    news_results = getNewsData(query, before, curr_date)

    news_str = ""

    for news in news_results:
        news_str += (
            f"### {news['title']} (source: {news['source']}) \n\n{news['snippet']}\n\n"
        )

    if len(news_results) == 0:
        return ""

    return f"## {query} Google News, from {before} to {curr_date}:\n\n{news_str}"


def get_reddit_global_news(
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
    max_limit_per_day: Annotated[int, "Maximum number of news per day"],
) -> str:
    """
    Retrieve the latest top reddit news
    Args:
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format
    Returns:
        str: A formatted dataframe containing the latest news articles posts on reddit and meta information in these columns: "created_utc", "id", "title", "selftext", "score", "num_comments", "url"
    """

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    before = start_date - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    posts = []
    # iterate from start_date to end_date
    curr_date = datetime.strptime(before, "%Y-%m-%d")

    total_iterations = (start_date - curr_date).days + 1
    pbar = tqdm(desc=f"Getting Global News on {start_date}", total=total_iterations)

    while curr_date <= start_date:
        curr_date_str = curr_date.strftime("%Y-%m-%d")
        fetch_result = fetch_top_from_category(
            "global_news",
            curr_date_str,
            max_limit_per_day,
            data_path=os.path.join(DATA_DIR, "reddit_data"),
        )
        posts.extend(fetch_result)
        curr_date += relativedelta(days=1)
        pbar.update(1)

    pbar.close()

    if len(posts) == 0:
        return ""

    news_str = ""
    for post in posts:
        if post["content"] == "":
            news_str += f"### {post['title']}\n\n"
        else:
            news_str += f"### {post['title']}\n\n{post['content']}\n\n"

    return f"## Global News Reddit, from {before} to {curr_date}:\n{news_str}"


def get_reddit_company_news(
    ticker: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
    max_limit_per_day: Annotated[int, "Maximum number of news per day"],
) -> str:
    """
    Retrieve the latest top reddit news
    Args:
        ticker: ticker symbol of the company
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format
    Returns:
        str: A formatted dataframe containing the latest news articles posts on reddit and meta information in these columns: "created_utc", "id", "title", "selftext", "score", "num_comments", "url"
    """

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    before = start_date - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    posts = []
    # iterate from start_date to end_date
    curr_date = datetime.strptime(before, "%Y-%m-%d")

    total_iterations = (start_date - curr_date).days + 1
    pbar = tqdm(
        desc=f"Getting Company News for {ticker} on {start_date}",
        total=total_iterations,
    )

    while curr_date <= start_date:
        curr_date_str = curr_date.strftime("%Y-%m-%d")
        fetch_result = fetch_top_from_category(
            "company_news",
            curr_date_str,
            max_limit_per_day,
            ticker,
            data_path=os.path.join(DATA_DIR, "reddit_data"),
        )
        posts.extend(fetch_result)
        curr_date += relativedelta(days=1)

        pbar.update(1)

    pbar.close()

    if len(posts) == 0:
        return ""

    news_str = ""
    for post in posts:
        if post["content"] == "":
            news_str += f"### {post['title']}\n\n"
        else:
            news_str += f"### {post['title']}\n\n{post['content']}\n\n"

    return f"##{ticker} News Reddit, from {before} to {curr_date}:\n\n{news_str}"


def get_stock_stats_indicators_window(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[
        str, "The current trading date you are trading on, YYYY-mm-dd"
    ],
    look_back_days: Annotated[int, "how many days to look back"],
    online: Annotated[bool, "to fetch data online or offline"],
) -> str:

    best_ind_params = {
        # Moving Averages
        "close_50_sma": (
            "50 SMA: A medium-term trend indicator. "
            "Usage: Identify trend direction and serve as dynamic support/resistance. "
            "Tips: It lags price; combine with faster indicators for timely signals."
        ),
        "close_200_sma": (
            "200 SMA: A long-term trend benchmark. "
            "Usage: Confirm overall market trend and identify golden/death cross setups. "
            "Tips: It reacts slowly; best for strategic trend confirmation rather than frequent trading entries."
        ),
        "close_10_ema": (
            "10 EMA: A responsive short-term average. "
            "Usage: Capture quick shifts in momentum and potential entry points. "
            "Tips: Prone to noise in choppy markets; use alongside longer averages for filtering false signals."
        ),
        # MACD Related
        "macd": (
            "MACD: Computes momentum via differences of EMAs. "
            "Usage: Look for crossovers and divergence as signals of trend changes. "
            "Tips: Confirm with other indicators in low-volatility or sideways markets."
        ),
        "macds": (
            "MACD Signal: An EMA smoothing of the MACD line. "
            "Usage: Use crossovers with the MACD line to trigger trades. "
            "Tips: Should be part of a broader strategy to avoid false positives."
        ),
        "macdh": (
            "MACD Histogram: Shows the gap between the MACD line and its signal. "
            "Usage: Visualize momentum strength and spot divergence early. "
            "Tips: Can be volatile; complement with additional filters in fast-moving markets."
        ),
        # Momentum Indicators
        "rsi": (
            "RSI: Measures momentum to flag overbought/oversold conditions. "
            "Usage: Apply 70/30 thresholds and watch for divergence to signal reversals. "
            "Tips: In strong trends, RSI may remain extreme; always cross-check with trend analysis."
        ),
        # Volatility Indicators
        "boll": (
            "Bollinger Middle: A 20 SMA serving as the basis for Bollinger Bands. "
            "Usage: Acts as a dynamic benchmark for price movement. "
            "Tips: Combine with the upper and lower bands to effectively spot breakouts or reversals."
        ),
        "boll_ub": (
            "Bollinger Upper Band: Typically 2 standard deviations above the middle line. "
            "Usage: Signals potential overbought conditions and breakout zones. "
            "Tips: Confirm signals with other tools; prices may ride the band in strong trends."
        ),
        "boll_lb": (
            "Bollinger Lower Band: Typically 2 standard deviations below the middle line. "
            "Usage: Indicates potential oversold conditions. "
            "Tips: Use additional analysis to avoid false reversal signals."
        ),
        "atr": (
            "ATR: Averages true range to measure volatility. "
            "Usage: Set stop-loss levels and adjust position sizes based on current market volatility. "
            "Tips: It's a reactive measure, so use it as part of a broader risk management strategy."
        ),
        # Volume-Based Indicators
        "vwma": (
            "VWMA: A moving average weighted by volume. "
            "Usage: Confirm trends by integrating price action with volume data. "
            "Tips: Watch for skewed results from volume spikes; use in combination with other volume analyses."
        ),
        "mfi": (
            "MFI: The Money Flow Index is a momentum indicator that uses both price and volume to measure buying and selling pressure. "
            "Usage: Identify overbought (>80) or oversold (<20) conditions and confirm the strength of trends or reversals. "
            "Tips: Use alongside RSI or MACD to confirm signals; divergence between price and MFI can indicate potential reversals."
        ),
    }

    if indicator not in best_ind_params:
        raise ValueError(
            f"Indicator {indicator} is not supported. Please choose from: {list(best_ind_params.keys())}"
        )

    end_date = curr_date
    curr_date = datetime.strptime(curr_date, "%Y-%m-%d")
    before = curr_date - relativedelta(days=look_back_days)

    if not online:
        # read from YFin data
        data = pd.read_csv(
            os.path.join(
                DATA_DIR,
                f"market_data/price_data/{symbol}-YFin-data-2015-01-01-2025-03-25.csv",
            )
        )
        data["Date"] = pd.to_datetime(data["Date"], utc=True)
        dates_in_df = data["Date"].astype(str).str[:10]

        ind_string = ""
        while curr_date >= before:
            # only do the trading dates
            if curr_date.strftime("%Y-%m-%d") in dates_in_df.values:
                indicator_value = get_stockstats_indicator(
                    symbol, indicator, curr_date.strftime("%Y-%m-%d"), online
                )

                ind_string += f"{curr_date.strftime('%Y-%m-%d')}: {indicator_value}\n"

            curr_date = curr_date - relativedelta(days=1)
    else:
        # online gathering
        ind_string = ""
        while curr_date >= before:
            indicator_value = get_stockstats_indicator(
                symbol, indicator, curr_date.strftime("%Y-%m-%d"), online
            )

            ind_string += f"{curr_date.strftime('%Y-%m-%d')}: {indicator_value}\n"

            curr_date = curr_date - relativedelta(days=1)

    result_str = (
        f"## {indicator} values from {before.strftime('%Y-%m-%d')} to {end_date}:\n\n"
        + ind_string
        + "\n\n"
        + best_ind_params.get(indicator, "No description available.")
    )

    return result_str


def get_stockstats_indicator(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[
        str, "The current trading date you are trading on, YYYY-mm-dd"
    ],
    online: Annotated[bool, "to fetch data online or offline"],
) -> str:

    curr_date = datetime.strptime(curr_date, "%Y-%m-%d")
    curr_date = curr_date.strftime("%Y-%m-%d")

    try:
        indicator_value = StockstatsUtils.get_stock_stats(
            symbol,
            indicator,
            curr_date,
            os.path.join(DATA_DIR, "market_data", "price_data"),
            online=online,
        )
    except Exception as e:
        print(
            f"Error getting stockstats indicator data for indicator {indicator} on {curr_date}: {e}"
        )
        return ""

    return str(indicator_value)


def get_YFin_data_window(
    symbol: Annotated[str, "ticker symbol of the company"],
    curr_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    # calculate past days
    date_obj = datetime.strptime(curr_date, "%Y-%m-%d")
    before = date_obj - relativedelta(days=look_back_days)
    start_date = before.strftime("%Y-%m-%d")

    # read in data
    data = pd.read_csv(
        os.path.join(
            DATA_DIR,
            f"market_data/price_data/{symbol}-YFin-data-2015-01-01-2025-03-25.csv",
        )
    )

    # Extract just the date part for comparison
    data["DateOnly"] = data["Date"].str[:10]

    # Filter data between the start and end dates (inclusive)
    filtered_data = data[
        (data["DateOnly"] >= start_date) & (data["DateOnly"] <= curr_date)
    ]

    # Drop the temporary column we created
    filtered_data = filtered_data.drop("DateOnly", axis=1)

    # Set pandas display options to show the full DataFrame
    with pd.option_context(
        "display.max_rows", None, "display.max_columns", None, "display.width", None
    ):
        df_string = filtered_data.to_string()

    return (
        f"## Raw Market Data for {symbol} from {start_date} to {curr_date}:\n\n"
        + df_string
    )


def get_YFin_data_online(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
):

    datetime.strptime(start_date, "%Y-%m-%d")
    datetime.strptime(end_date, "%Y-%m-%d")

    # Create ticker object
    ticker = yf.Ticker(symbol.upper())

    # Fetch historical data for the specified date range
    data = ticker.history(start=start_date, end=end_date)

    # Check if data is empty
    if data.empty:
        return (
            f"No data found for symbol '{symbol}' between {start_date} and {end_date}"
        )

    # Remove timezone info from index for cleaner output
    if data.index.tz is not None:
        data.index = data.index.tz_localize(None)

    # Round numerical values to 2 decimal places for cleaner display
    numeric_columns = ["Open", "High", "Low", "Close", "Adj Close"]
    for col in numeric_columns:
        if col in data.columns:
            data[col] = data[col].round(2)

    # Convert DataFrame to CSV string
    csv_string = data.to_csv()

    # Add header information
    header = f"# Stock data for {symbol.upper()} from {start_date} to {end_date}\n"
    header += f"# Total records: {len(data)}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    return header + csv_string


def get_YFin_data(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    # read in data
    data = pd.read_csv(
        os.path.join(
            DATA_DIR,
            f"market_data/price_data/{symbol}-YFin-data-2015-01-01-2025-03-25.csv",
        )
    )

    if end_date > "2025-03-25":
        raise Exception(
            f"Get_YFin_Data: {end_date} is outside of the data range of 2015-01-01 to 2025-03-25"
        )

    # Extract just the date part for comparison
    data["DateOnly"] = data["Date"].str[:10]

    # Filter data between the start and end dates (inclusive)
    filtered_data = data[
        (data["DateOnly"] >= start_date) & (data["DateOnly"] <= end_date)
    ]

    # Drop the temporary column we created
    filtered_data = filtered_data.drop("DateOnly", axis=1)

    # remove the index from the dataframe
    filtered_data = filtered_data.reset_index(drop=True)

    return filtered_data


def get_stock_news_openai(ticker, curr_date):
    config = get_config()
    client = OpenAI(base_url=config["backend_url"])

    response = client.responses.create(
        model=config["quick_think_llm"],
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"Can you search Social Media for {ticker} from 7 days before {curr_date} to {curr_date}? Make sure you only get the data posted during that period.",
                    }
                ],
            }
        ],
        text={"format": {"type": "text"}},
        reasoning={},
        tools=[
            {
                "type": "web_search_preview",
                "user_location": {"type": "approximate"},
                "search_context_size": "low",
            }
        ],
        temperature=1,
        max_output_tokens=4096,
        top_p=1,
        store=True,
    )

    return response.output[1].content[0].text


def get_global_news_openai(curr_date):
    config = get_config()
    client = OpenAI(base_url=config["backend_url"])

    response = client.responses.create(
        model=config["quick_think_llm"],
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"Can you search global or macroeconomics news from 7 days before {curr_date} to {curr_date} that would be informative for trading purposes? Make sure you only get the data posted during that period.",
                    }
                ],
            }
        ],
        text={"format": {"type": "text"}},
        reasoning={},
        tools=[
            {
                "type": "web_search_preview",
                "user_location": {"type": "approximate"},
                "search_context_size": "low",
            }
        ],
        temperature=1,
        max_output_tokens=4096,
        top_p=1,
        store=True,
    )

    return response.output[1].content[0].text


def get_fundamentals_openai(ticker, curr_date):
    config = get_config()
    client = OpenAI(base_url=config["backend_url"])

    response = client.responses.create(
        model=config["quick_think_llm"],
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"Can you search Fundamental for discussions on {ticker} during of the month before {curr_date} to the month of {curr_date}. Make sure you only get the data posted during that period. List as a table, with PE/PS/Cash flow/ etc",
                    }
                ],
            }
        ],
        text={"format": {"type": "text"}},
        reasoning={},
        tools=[
            {
                "type": "web_search_preview",
                "user_location": {"type": "approximate"},
                "search_context_size": "low",
            }
        ],
        temperature=1,
        max_output_tokens=4096,
        top_p=1,
        store=True,
    )

    return response.output[1].content[0].text
