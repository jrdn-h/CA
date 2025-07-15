#!/usr/bin/env python3
"""
Simple validation test for TradingAgents crypto integration.
This verifies core functionality works without external dependencies.
"""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_basic_imports():
    """Test that all core modules can be imported."""
    print("🔧 Testing basic imports...")
    
    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        print("   ✅ TradingAgentsGraph imported successfully")
        
        from tradingagents.default_config import DEFAULT_CONFIG
        print("   ✅ DEFAULT_CONFIG imported successfully")
        
        from tradingagents.dataflows.ccxt_adapters import CCXTAdapters
        print("   ✅ CCXTAdapters imported successfully")
        
        from tradingagents.dataflows.crypto_cache import CryptoCacheManager
        print("   ✅ CryptoCacheManager imported successfully")
        
        return True
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False

def test_basic_initialization():
    """Test basic framework initialization."""
    print("\n🚀 Testing basic framework initialization...")
    
    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # Create minimal config
        test_config = DEFAULT_CONFIG.copy()
        test_config.update({
            "use_crypto": True,
            "online_tools": False,  # Disable to avoid API calls
            "redis_caching": False,  # Disable to avoid Redis dependency
            "max_debate_rounds": 1,
            "data_dir": "./simple_test_data"
        })
        
        # Initialize framework
        graph = TradingAgentsGraph(
            selected_analysts=["market"],  # Just one analyst
            config=test_config,
            debug=False
        )
        
        print(f"   ✅ Framework initialized with crypto mode: {graph.config.get('use_crypto')}")
        print(f"   📡 Tool nodes available: {list(graph.tool_nodes.keys())}")
        
        return True
    except Exception as e:
        print(f"   ❌ Initialization failed: {e}")
        return False

def test_component_creation():
    """Test individual component creation."""
    print("\n🔧 Testing component creation...")
    
    try:
        from tradingagents.dataflows.ccxt_adapters import CCXTAdapters
        from tradingagents.dataflows.crypto_cache import CryptoCacheManager
        
        # Test CCXT Adapters
        adapters = CCXTAdapters()
        print("   ✅ CCXTAdapters created successfully")
        
        # Test Cache Manager (should work even without Redis)
        cache_manager = CryptoCacheManager(redis_host="invalid", redis_port=9999)
        print(f"   ✅ CryptoCacheManager created (cache_enabled: {cache_manager.cache_enabled})")
        
        return True
    except Exception as e:
        print(f"   ❌ Component creation failed: {e}")
        return False

def run_simple_validation():
    """Run simple validation tests."""
    print("🎯 SIMPLE CRYPTO INTEGRATION VALIDATION")
    print("=" * 50)
    
    test_results = []
    
    # Run tests
    test_results.append(("Basic Imports", test_basic_imports()))
    test_results.append(("Framework Initialization", test_basic_initialization()))
    test_results.append(("Component Creation", test_component_creation()))
    
    # Report results
    print("\n" + "=" * 50)
    print("📋 VALIDATION RESULTS")
    print("=" * 50)
    
    passed_tests = 0
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} | {test_name}")
        if passed:
            passed_tests += 1
    
    print(f"\n📊 Tests passed: {passed_tests}/{len(test_results)}")
    
    if passed_tests == len(test_results):
        print("\n🎉 ALL VALIDATION TESTS PASSED!")
        print("✨ Core crypto integration is working correctly!")
        print("🚀 Ready for more comprehensive testing!")
        return True
    else:
        print("\n⚠️  Some validation tests failed.")
        print("Please check the error messages above.")
        return False

if __name__ == "__main__":
    success = run_simple_validation()
    if not success:
        sys.exit(1) 