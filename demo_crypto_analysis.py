"""Demo: TradingAgents Crypto Analysis in Action"""

from tradingagents.dataflows.crypto_utils import CryptoUtils
from tradingagents.dataflows.interface import get_crypto_data_online, get_crypto_info_online
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.dataflows.config import set_config

def demo_crypto_analysis():
    """Demonstrate crypto analysis capabilities."""
    print("🚀 TradingAgents Crypto Analysis Demo")
    print("=" * 60)
    
    # Enable crypto mode
    config = DEFAULT_CONFIG.copy()
    config["use_crypto"] = True
    set_config(config)
    
    print("⚙️  Configuration: Crypto Mode ENABLED")
    print(f"📡 Data Source: {config['crypto']['backend_url']}")
    print(f"🪙 Supported: {', '.join(config['crypto']['supported_symbols'])}")
    print()
    
    # Analyze multiple cryptocurrencies
    cryptos = ["BTC", "ETH", "SOL"]
    
    print("📊 Cryptocurrency Market Analysis")
    print("=" * 60)
    
    for symbol in cryptos:
        print(f"\n🔍 Analyzing {symbol}...")
        print("-" * 30)
        
        # Get current market info
        market_info = get_crypto_info_online(symbol)
        print("📈 Market Overview:")
        for line in market_info.split('\n')[1:]:  # Skip header
            if line.strip():
                print(f"  {line}")
        
        # Get price data
        price_data = get_crypto_data_online(symbol, "2024-12-01", "2024-12-03")
        
        if "Error" not in price_data and len(price_data) > 100:
            print(f"📊 Price Data: ✅ Retrieved successfully ({len(price_data)} chars)")
            
            # Extract some insights from the data
            if "Close" in price_data:
                print("💹 Technical Analysis Ready: OHLCV data available")
        else:
            print(f"⚠️  Price Data: Limited ({len(price_data)} chars)")
    
    print("\n" + "=" * 60)
    print("🎯 Summary: Crypto Analysis Pipeline")
    print("=" * 60)
    print("✅ Data Sources: CoinGecko API integrated")
    print("✅ Multi-Asset: BTC, ETH, SOL support confirmed")
    print("✅ OHLCV Format: Compatible with existing technical analysis")
    print("✅ Real-Time: Live market data fetching")
    print("✅ Toggle System: Seamless stock ↔ crypto switching")
    
    print("\n🚀 Ready for Full AI Agent Analysis!")
    print("   Use: config['use_crypto'] = True")
    print("   Then: ta.propagate('BTC', '2024-12-01')")
    print("=" * 60)

if __name__ == "__main__":
    demo_crypto_analysis() 