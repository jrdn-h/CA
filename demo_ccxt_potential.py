#!/usr/bin/env python3
"""Demo showcasing CCXT adapters potential for advanced trading analysis."""

import sys
import os
import asyncio
import json
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tradingagents.dataflows.ccxt_adapters import CCXTAdapters, ExchangeConfig


def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print('='*60)


def demo_exchange_ecosystem():
    """Demo 1: Show the exchange ecosystem supported by CCXT adapters."""
    print_header("Exchange Ecosystem Overview")
    
    adapters = CCXTAdapters()
    exchanges = adapters.get_supported_exchanges()
    
    print("📊 Supported Cryptocurrency Exchanges:")
    print()
    
    for exchange in exchanges:
        sandbox_status = "🧪 Sandbox" if exchange['sandbox_available'] else "🔴 Live Only"
        
        print(f"🏦 {exchange['name'].upper()}")
        print(f"   📈 OHLCV Data: {'✅' if exchange['has_ohlcv'] else '❌'}")
        print(f"   📚 Order Book: {'✅' if exchange['has_order_book'] else '❌'}")
        print(f"   ⚡ Rate Limit: {exchange['rate_limit_per_minute']:,} req/min")
        print(f"   💰 Trading Fees: {exchange['trading_fees']*100:.2f}%")
        print(f"   🛡️  Environment: {sandbox_status}")
        print()
    
    print(f"🌐 Total Exchanges: {len(exchanges)}")
    print("💡 Pro Tip: Use sandbox environments for testing strategies!")


def demo_multi_timeframe_analysis():
    """Demo 2: Multi-timeframe OHLCV analysis."""
    print_header("Multi-Timeframe Technical Analysis")
    
    adapters = CCXTAdapters()
    symbol = 'BTC/USDT'
    exchange = 'binance'
    
    timeframes = ['1h', '4h', '1d']
    
    print(f"📊 Analyzing {symbol} across multiple timeframes on {exchange.upper()}:")
    print()
    
    for timeframe in timeframes:
        try:
            print(f"⏰ {timeframe} Timeframe Analysis:")
            
            # Fetch data
            df = adapters.fetch_ohlcv(exchange, symbol, timeframe=timeframe, limit=20)
            
            if len(df) > 0:
                latest = df.iloc[-1]
                previous = df.iloc[-2] if len(df) > 1 else latest
                
                # Calculate basic indicators
                price_change = latest['close'] - previous['close']
                price_change_pct = (price_change / previous['close']) * 100
                
                avg_volume = df['volume'].tail(5).mean()
                volume_trend = "📈 High" if latest['volume'] > avg_volume * 1.2 else "📉 Low" if latest['volume'] < avg_volume * 0.8 else "📊 Normal"
                
                volatility = ((df['high'] - df['low']) / df['close'] * 100).tail(5).mean()
                
                print(f"   💰 Current Price: ${latest['close']:,.2f}")
                print(f"   📈 Price Change: {price_change:+.2f} ({price_change_pct:+.2f}%)")
                print(f"   📊 Volume Status: {volume_trend}")
                print(f"   ⚡ Avg Volatility: {volatility:.2f}%")
                print(f"   📅 Last Update: {df.index[-1].strftime('%Y-%m-%d %H:%M UTC')}")
            else:
                print("   ⚠️  No data available")
            
            print()
            
        except Exception as e:
            print(f"   ❌ Error fetching {timeframe} data: {e}")
            print()


def demo_order_book_intelligence():
    """Demo 3: Advanced order book analysis."""
    print_header("Order Book Intelligence & Market Microstructure")
    
    adapters = CCXTAdapters()
    symbol = 'BTC/USDT'
    exchange = 'binance'
    
    try:
        print(f"📚 Deep Order Book Analysis for {symbol} on {exchange.upper()}:")
        print()
        
        # Fetch order book
        order_book = adapters.fetch_order_book(exchange, symbol, limit=20)
        
        # Spread Analysis
        spread = order_book['spread']
        print("💰 SPREAD ANALYSIS:")
        print(f"   Best Bid: ${spread['best_bid']:,.2f}")
        print(f"   Best Ask: ${spread['best_ask']:,.2f}")
        print(f"   Absolute Spread: ${spread['absolute']:.2f}")
        print(f"   Spread %: {spread['percentage']:.4f}%")
        print()
        
        # Volume Analysis
        volume = order_book['volume_analysis']
        print("📊 VOLUME DYNAMICS:")
        print(f"   Bid Volume (Top 10): {volume['bid_volume_top10']:,.2f}")
        print(f"   Ask Volume (Top 10): {volume['ask_volume_top10']:,.2f}")
        print(f"   Volume Imbalance: {volume['volume_imbalance']:+.3f}")
        print(f"   Market Signal: {volume['imbalance_signal']}")
        print()
        
        # Depth Analysis
        depth = order_book['depth_analysis']
        print("🏊 MARKET DEPTH:")
        print(f"   Bid Depth (Top 5): ${depth['bid_depth_top5']:,.0f}")
        print(f"   Ask Depth (Top 5): ${depth['ask_depth_top5']:,.0f}")
        print(f"   Total Depth: ${depth['total_depth']:,.0f}")
        print(f"   Depth Ratio: {depth['depth_ratio']:.2f}")
        print()
        
        # Market Quality
        quality = order_book['market_quality']
        print("⭐ MARKET QUALITY METRICS:")
        print(f"   Spread Category: {quality['spread_category']}")
        print(f"   Liquidity Score: {quality['liquidity_score']:.1f}/100")
        print(f"   Order Book Levels: {quality['order_book_levels']}")
        print()
        
        # Trading Insights
        print("🧠 AI TRADING INSIGHTS:")
        if volume['imbalance_signal'] == 'BULLISH':
            print("   🐂 More buyers than sellers - potential upward pressure")
        elif volume['imbalance_signal'] == 'BEARISH':
            print("   🐻 More sellers than buyers - potential downward pressure")
        else:
            print("   ⚖️  Balanced order flow - stable market conditions")
        
        if quality['spread_category'] == 'TIGHT':
            print("   ✨ Excellent liquidity - low trading costs")
        elif quality['spread_category'] == 'WIDE':
            print("   ⚠️  Poor liquidity - higher trading costs")
        
        print()
        
    except Exception as e:
        print(f"❌ Order book analysis failed: {e}")
        print("   This may happen if the exchange is not accessible")


def demo_arbitrage_scanner():
    """Demo 4: Cross-exchange arbitrage opportunities."""
    print_header("Cross-Exchange Arbitrage Scanner")
    
    adapters = CCXTAdapters()
    symbol = 'BTC/USDT'
    target_exchanges = ['binance', 'kraken']  # Start with 2 reliable exchanges
    
    try:
        print(f"🔍 Scanning for arbitrage opportunities: {symbol}")
        print(f"📡 Target exchanges: {', '.join(target_exchanges)}")
        print()
        
        # Get exchange comparison
        comparison = adapters.get_exchange_comparison(symbol, exchanges=target_exchanges)
        
        print("📊 EXCHANGE COMPARISON:")
        exchanges_data = comparison['exchanges']
        
        successful_count = 0
        for exchange_name, data in exchanges_data.items():
            if 'error' not in data:
                successful_count += 1
                print(f"🏦 {exchange_name.upper()}:")
                print(f"   💰 Price: ${data['price']:,.2f}")
                print(f"   📈 Spread: {data['spread_pct']:.3f}%")
                print(f"   💧 Liquidity: ${data['liquidity']:,.0f}")
                print(f"   ⚖️  Volume Signal: {data['volume_imbalance']:+.3f}")
                print(f"   ⭐ Quality: {data['market_quality']['spread_category']}")
            else:
                print(f"🏦 {exchange_name.upper()}: ❌ {data['error']}")
            print()
        
        # Arbitrage opportunities
        arbitrage_ops = comparison.get('arbitrage_opportunities', [])
        
        if arbitrage_ops:
            print("💰 ARBITRAGE OPPORTUNITIES DETECTED:")
            for i, op in enumerate(arbitrage_ops, 1):
                profit_potential = op['potential_profit']
                profit_indicator = "🟢" if profit_potential > 0.5 else "🟡" if profit_potential > 0.1 else "🔴"
                
                print(f"   {profit_indicator} Opportunity #{i}:")
                print(f"      📉 Buy on: {op['buy_exchange'].upper()}")
                print(f"      📈 Sell on: {op['sell_exchange'].upper()}")
                print(f"      💱 Price Difference: {op['price_difference_pct']:.2f}%")
                print(f"      💰 Est. Profit: {profit_potential:.2f}%")
                print()
        else:
            print("📊 No significant arbitrage opportunities found")
            if successful_count >= 2:
                print("   Market prices are well-aligned across exchanges")
            print()
        
        # Best venues
        if comparison.get('best_liquidity'):
            best_liquidity = comparison['best_liquidity']
            print(f"🏆 Best Liquidity: {best_liquidity[0].upper()} (${best_liquidity[1]:,.0f})")
        
        if comparison.get('tightest_spread'):
            tightest_spread = comparison['tightest_spread']
            print(f"⚡ Tightest Spread: {tightest_spread[0].upper()} ({tightest_spread[1]:.3f}%)")
        
        print()
        
    except Exception as e:
        print(f"❌ Arbitrage scanner failed: {e}")
        print("   This may happen if exchanges are not accessible")


def demo_trading_strategy_insights():
    """Demo 5: AI-powered trading strategy insights."""
    print_header("AI-Powered Trading Strategy Insights")
    
    print("🧠 Advanced Trading Intelligence powered by CCXT Adapters:")
    print()
    
    strategies = [
        {
            'name': 'Market Making',
            'description': 'Use tight spreads from order book data to place profitable buy/sell orders',
            'data_sources': ['Order Book Depth', 'Spread Analysis', 'Volume Imbalance'],
            'edge': 'Real-time spread monitoring across exchanges'
        },
        {
            'name': 'Arbitrage Trading',
            'description': 'Exploit price differences between exchanges',
            'data_sources': ['Multi-Exchange Pricing', 'Liquidity Analysis', 'Trading Fees'],
            'edge': 'Cross-exchange price monitoring with latency optimization'
        },
        {
            'name': 'Momentum Trading',
            'description': 'Follow strong price movements using multi-timeframe analysis',
            'data_sources': ['Multi-Timeframe OHLCV', 'Volume Trends', 'Volatility Metrics'],
            'edge': 'Real-time trend detection across timeframes'
        },
        {
            'name': 'Liquidity Mining',
            'description': 'Provide liquidity where it\'s most needed and profitable',
            'data_sources': ['Order Book Depth', 'Market Quality Metrics', 'Spread Categories'],
            'edge': 'Dynamic liquidity allocation based on market conditions'
        }
    ]
    
    for i, strategy in enumerate(strategies, 1):
        print(f"🎯 STRATEGY #{i}: {strategy['name']}")
        print(f"   📝 Description: {strategy['description']}")
        print(f"   📊 Data Sources: {', '.join(strategy['data_sources'])}")
        print(f"   ⚡ Competitive Edge: {strategy['edge']}")
        print()
    
    print("💡 Key Advantages of CCXT Integration:")
    print("   🌐 Multi-Exchange Coverage: Access to 5+ major exchanges")
    print("   ⚡ Real-Time Data: Sub-second order book updates")
    print("   🧠 Smart Caching: Redis-powered performance optimization")
    print("   📊 Rich Analytics: Advanced market microstructure insights")
    print("   🔧 Production Ready: Rate limiting, error handling, fallbacks")
    print()
    
    print("🚀 Next Steps for Traders:")
    print("   1. 🧪 Test strategies in sandbox environments")
    print("   2. 📊 Monitor multiple exchanges simultaneously")
    print("   3. ⚡ Implement low-latency execution pipelines")
    print("   4. 🔄 Optimize based on real market microstructure data")


def main():
    """Run the comprehensive CCXT adapters demo."""
    print("🌟 Welcome to CCXT Adapters - Advanced Crypto Trading Infrastructure")
    print("🚀 Powering next-generation cryptocurrency trading strategies")
    print()
    
    try:
        # Run all demos
        demo_exchange_ecosystem()
        demo_multi_timeframe_analysis()
        demo_order_book_intelligence()
        demo_arbitrage_scanner()
        demo_trading_strategy_insights()
        
        print_header("Demo Complete!")
        print("✨ CCXT Adapters are now ready for production trading!")
        print()
        print("🔧 Integration Points:")
        print("   • Import: from tradingagents.dataflows.ccxt_adapters import CCXTAdapters")
        print("   • Initialize: adapters = CCXTAdapters()")
        print("   • Fetch OHLCV: adapters.fetch_ohlcv('binance', 'BTC/USDT')")
        print("   • Order Book: adapters.fetch_order_book('binance', 'BTC/USDT')")
        print("   • Compare: adapters.get_exchange_comparison('BTC/USDT')")
        print()
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("   This is expected if running without internet access")
    
    print("🎉 Thanks for exploring CCXT Adapters!")


if __name__ == "__main__":
    main() 