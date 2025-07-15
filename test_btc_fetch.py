"""Test BTC OHLCV data fetching from CoinGecko."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.crypto_utils import CryptoUtils
from datetime import datetime, timedelta

def test_btc_fetch():
    """Test fetching BTC data."""
    print("🚀 Testing BTC OHLCV Fetch")
    print("=" * 40)
    
    crypto_utils = CryptoUtils()
    
    # Test with recent dates
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    print(f"📊 Fetching BTC data from {start_date} to {end_date}")
    
    try:
        # Fetch BTC data
        btc_data = crypto_utils.get_crypto_data("BTC", start_date, end_date)
        
        print(f"✅ Data fetched successfully!")
        print(f"📈 Shape: {btc_data.shape}")
        print(f"🔍 Columns: {list(btc_data.columns)}")
        
        if not btc_data.empty:
            print(f"📋 Sample data:")
            print(btc_data.head())
            print(f"💰 Latest BTC price: ${btc_data['Close'].iloc[-1]:,.2f}")
        else:
            print("⚠️  No data returned (empty DataFrame)")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_btc_fetch()
    if success:
        print("\n✨ BTC fetch test completed!")
    else:
        print("\n⚠️  BTC fetch test failed!") 