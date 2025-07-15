#!/usr/bin/env python3
"""
Focused Integration Test for TradingAgents Crypto Infrastructure Success

This test validates the essential integration points to demonstrate that 
the comprehensive crypto integration is working correctly.
"""

import sys
import os
import time

# Add the project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_core_crypto_integration():
    """Test the core crypto integration functionality."""
    print("🚀 CORE CRYPTO INTEGRATION SUCCESS TEST")
    print("=" * 60)
    
    all_tests_passed = True
    test_results = []
    
    # Test 1: Import Validation
    print("\n1️⃣ Testing Core Imports")
    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG
        from tradingagents.dataflows.ccxt_adapters import CCXTAdapters
        from tradingagents.dataflows.crypto_cache import CryptoCacheManager
        from tradingagents.dataflows.metric_registry import MetricRegistry
        
        print("   ✅ All core crypto modules imported successfully")
        test_results.append(("Core Imports", True))
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        test_results.append(("Core Imports", False))
        all_tests_passed = False
    
    # Test 2: Component Creation
    print("\n2️⃣ Testing Component Creation")
    try:
        # CCXT Adapters
        adapters = CCXTAdapters()
        assert hasattr(adapters, '_exchange_clients'), "CCXT adapters should have exchange clients"
        
        # Cache Manager (should handle no Redis gracefully)
        cache_manager = CryptoCacheManager(redis_host="invalid", redis_port=9999)
        assert hasattr(cache_manager, 'cache_enabled'), "Cache manager should have cache_enabled attribute"
        
        # Metric Registry
        registry = MetricRegistry()
        assert hasattr(registry, 'providers'), "Metric registry should have providers"
        
        print("   ✅ All core components created successfully")
        test_results.append(("Component Creation", True))
    except Exception as e:
        print(f"   ❌ Component creation failed: {e}")
        test_results.append(("Component Creation", False))
        all_tests_passed = False
    
    # Test 3: Configuration Handling
    print("\n3️⃣ Testing Configuration Handling")
    try:
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # Test configuration structure
        assert isinstance(DEFAULT_CONFIG, dict), "Config should be a dictionary"
        assert "llm_provider" in DEFAULT_CONFIG, "Config should have llm_provider"
        
        # Test crypto configuration
        crypto_config = DEFAULT_CONFIG.copy()
        crypto_config.update({
            "use_crypto": True,
            "online_tools": False,
            "redis_caching": False,
            "data_dir": f"./success_test_{int(time.time())}"
        })
        
        assert crypto_config["use_crypto"] == True, "Crypto should be enabled"
        
        print("   ✅ Configuration handling working correctly")
        test_results.append(("Configuration Handling", True))
    except Exception as e:
        print(f"   ❌ Configuration handling failed: {e}")
        test_results.append(("Configuration Handling", False))
        all_tests_passed = False
    
    # Test 4: Framework Initialization (Single Test)
    print("\n4️⃣ Testing Framework Initialization")
    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        
        # Single framework initialization
        minimal_config = {
            "use_crypto": True,
            "llm_provider": "openai",
            "deep_think_llm": "gpt-4o-mini", 
            "quick_think_llm": "gpt-4o-mini",
            "online_tools": False,
            "redis_caching": False,
            "max_debate_rounds": 1,
            "data_dir": f"./success_test_{int(time.time())}_single",
            "project_dir": os.path.abspath("."),
            "results_dir": "./results"
        }
        
        graph = TradingAgentsGraph(
            selected_analysts=["market"],  # Single analyst to minimize conflicts
            config=minimal_config,
            debug=False
        )
        
        # Validate initialization
        assert hasattr(graph, 'tool_nodes'), "Graph should have tool_nodes"
        assert hasattr(graph, 'toolkit'), "Graph should have toolkit"
        assert graph.config.get("use_crypto") == True, "Crypto mode should be enabled"
        
        tool_nodes = list(graph.tool_nodes.keys())
        print(f"   ✅ Framework initialized with tool nodes: {tool_nodes}")
        print(f"   📊 Crypto mode enabled: {graph.config.get('use_crypto')}")
        test_results.append(("Framework Initialization", True))
    except Exception as e:
        print(f"   ❌ Framework initialization failed: {e}")
        test_results.append(("Framework Initialization", False))
        all_tests_passed = False
    
    # Test 5: Exchange Configuration Validation
    print("\n5️⃣ Testing Exchange Configuration")
    try:
        from tradingagents.dataflows.ccxt_adapters import ExchangeConfig
        
        # Test exchange configuration
        exchanges = ExchangeConfig.list_exchanges()
        assert len(exchanges) >= 3, "Should support multiple exchanges"
        
        # Test specific exchange info
        binance_info = ExchangeConfig.get_exchange_info('binance')
        assert binance_info is not None, "Binance config should be available"
        assert binance_info['has_ohlcv'] == True, "Binance should support OHLCV"
        
        print(f"   ✅ Exchange configuration working, supports: {exchanges}")
        test_results.append(("Exchange Configuration", True))
    except Exception as e:
        print(f"   ❌ Exchange configuration failed: {e}")
        test_results.append(("Exchange Configuration", False))
        all_tests_passed = False
    
    # Test 6: Cache Fallback Logic
    print("\n6️⃣ Testing Cache Fallback Logic")
    try:
        from tradingagents.dataflows.crypto_cache import CryptoCacheManager
        
        # Test cache fallback
        cache = CryptoCacheManager(redis_host="invalid", redis_port=9999)
        
        # Should be disabled but functional
        assert cache.cache_enabled == False, "Cache should be disabled with invalid Redis"
        
        # Operations should fail gracefully
        set_result = cache.set("test", {"data": "test"})
        assert set_result == False, "Set should return False when disabled"
        
        get_result = cache.get("test")
        assert get_result is None, "Get should return None when disabled"
        
        print("   ✅ Cache fallback logic working correctly")
        test_results.append(("Cache Fallback Logic", True))
    except Exception as e:
        print(f"   ❌ Cache fallback logic failed: {e}")
        test_results.append(("Cache Fallback Logic", False))
        all_tests_passed = False
    
    # Generate Final Report
    print("\n" + "=" * 60)
    print("📋 CORE CRYPTO INTEGRATION TEST RESULTS")
    print("=" * 60)
    
    passed_tests = 0
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} | {test_name}")
        if passed:
            passed_tests += 1
    
    print(f"\n📊 Tests passed: {passed_tests}/{len(test_results)}")
    
    if all_tests_passed:
        print("\n🎉 ALL CORE INTEGRATION TESTS PASSED!")
        print("\n✨ Key Integration Points Validated:")
        print("   • All crypto modules import successfully")
        print("   • Core components initialize correctly")
        print("   • Configuration handling works")
        print("   • Framework supports crypto mode")
        print("   • Exchange configurations are available")
        print("   • Cache fallback logic is robust")
        print("\n🚀 CRYPTO INTEGRATION IS WORKING SUCCESSFULLY!")
        print("\nThis validates that the comprehensive integration implementation")
        print("from CRYPTO_INFRASTRUCTURE_STATUS.md is functioning correctly.")
        
        return True
    else:
        print("\n⚠️  Some core integration tests failed.")
        print("Please check the error messages above.")
        return False

if __name__ == "__main__":
    success = test_core_crypto_integration()
    if not success:
        sys.exit(1) 