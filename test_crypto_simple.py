"""Simple focused test for crypto pipeline functionality."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.crypto_utils import CryptoUtils
from tradingagents.dataflows.interface import get_crypto_data_online, get_crypto_info_online
from tradingagents.agents.utils.agent_utils import Toolkit
from tradingagents.default_config import DEFAULT_CONFIG

def test_crypto_data_layer():
    """Test the crypto data layer directly."""
    print("🔍 Testing Crypto Data Layer")
    print("=" * 40)
    
    try:
        # Test CryptoUtils directly
        print("📊 Test: CryptoUtils...")
        crypto_utils = CryptoUtils()
        btc_data = crypto_utils.get_crypto_data("BTC", "2024-12-01", "2024-12-03")
        print(f"  ✅ BTC OHLCV data: {btc_data.shape} shape")
        
        btc_info = crypto_utils.get_crypto_info("BTC")
        print(f"  ✅ BTC info: {btc_info.get('name', 'N/A')} at ${btc_info.get('current_price', 0):,.2f}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Crypto data layer failed: {e}")
        return False

def test_crypto_interface():
    """Test the crypto interface functions."""
    print("\n🔗 Testing Crypto Interface")
    print("=" * 40)
    
    try:
        # Test with crypto enabled config
        from tradingagents.dataflows.config import set_config
        
        config = DEFAULT_CONFIG.copy()
        config["use_crypto"] = True
        set_config(config)
        
        print("📊 Test: Interface functions...")
        data_result = get_crypto_data_online("BTC", "2024-12-01", "2024-12-03")
        print(f"  ✅ Data interface: {len(data_result)} characters")
        
        info_result = get_crypto_info_online("BTC")
        print(f"  ✅ Info interface: {len(info_result)} characters")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Crypto interface failed: {e}")
        return False

def test_crypto_tools():
    """Test the crypto tools in Toolkit."""
    print("\n🛠️  Testing Crypto Tools")
    print("=" * 40)
    
    try:
        # Test Toolkit crypto methods
        print("📊 Test: Toolkit crypto tools...")
        
        toolkit = Toolkit()
        
        data_result = toolkit.get_crypto_data_online.invoke({
            "symbol": "BTC", 
            "start_date": "2024-12-01", 
            "end_date": "2024-12-03"
        })
        print(f"  ✅ Toolkit data: {len(data_result)} characters")
        
        info_result = toolkit.get_crypto_info_online.invoke({"symbol": "BTC"})
        print(f"  ✅ Toolkit info: {len(info_result)} characters")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Crypto tools failed: {e}")
        return False

def test_crypto_config():
    """Test crypto configuration."""
    print("\n⚙️  Testing Crypto Configuration")
    print("=" * 40)
    
    try:
        # Test config structure
        print("📊 Test: Config structure...")
        config = DEFAULT_CONFIG.copy()
        
        assert "use_crypto" in config, "Missing use_crypto flag"
        assert "crypto" in config, "Missing crypto config section"
        
        crypto_config = config["crypto"]
        assert "backend_url" in crypto_config, "Missing backend_url"
        assert "symbol_mapping" in crypto_config, "Missing symbol_mapping"
        
        print(f"  ✅ Config structure valid")
        print(f"  - Use crypto: {config['use_crypto']}")
        print(f"  - Backend URL: {crypto_config['backend_url']}")
        print(f"  - Supported symbols: {len(crypto_config['supported_symbols'])}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Config test failed: {e}")
        return False

def test_crypto_vs_stock_mode():
    """Test crypto vs stock mode toggle."""
    print("\n🔄 Testing Mode Toggle")
    print("=" * 40)
    
    try:
        from tradingagents.dataflows.config import set_config
        
        # Test stock mode
        print("📊 Test: Stock mode...")
        stock_config = DEFAULT_CONFIG.copy()
        stock_config["use_crypto"] = False
        set_config(stock_config)
        
        stock_result = get_crypto_data_online("BTC", "2024-12-01", "2024-12-03")
        print(f"  - Stock mode result: {stock_result}")
        assert "not enabled" in stock_result, "Stock mode should disable crypto"
        print(f"  ✅ Stock mode correctly disabled crypto")
        
        # Test crypto mode
        print("📊 Test: Crypto mode...")
        crypto_config = DEFAULT_CONFIG.copy()
        crypto_config["use_crypto"] = True
        set_config(crypto_config)
        
        crypto_result = get_crypto_data_online("BTC", "2024-12-01", "2024-12-03")
        print(f"  - Crypto mode result length: {len(crypto_result)}")
        assert "not enabled" not in crypto_result, "Crypto mode should enable crypto"
        print(f"  ✅ Crypto mode correctly enabled crypto")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Mode toggle failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Crypto Pipeline Simple Tests")
    print("=" * 50)
    
    tests = [
        ("Config", test_crypto_config),
        ("Data Layer", test_crypto_data_layer),
        ("Interface", test_crypto_interface),
        ("Tools", test_crypto_tools),
        ("Mode Toggle", test_crypto_vs_stock_mode),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    print("\n📋 Test Results Summary:")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  - {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All crypto pipeline tests PASSED!")
        print("🚀 Crypto functionality is working correctly!")
    else:
        print("⚠️  Some tests failed. Crypto pipeline needs fixes.")
    print("=" * 50) 