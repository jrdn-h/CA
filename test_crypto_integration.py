"""Integration test for crypto pipeline end-to-end functionality."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

def test_crypto_integration():
    """Test the complete crypto pipeline with BTC."""
    print("🚀 Testing Crypto Integration Pipeline")
    print("=" * 60)
    
    # Create crypto-enabled config
    config = DEFAULT_CONFIG.copy()
    config["use_crypto"] = True  # Enable crypto mode
    config["llm_provider"] = "openai"
    config["deep_think_llm"] = "gpt-4o-mini"  # Cost-effective for testing
    config["quick_think_llm"] = "gpt-4o-mini"
    config["max_debate_rounds"] = 1
    config["online_tools"] = True
    
    print(f"🔧 Configuration:")
    print(f"  - Crypto Mode: {config['use_crypto']}")
    print(f"  - LLM Provider: {config['llm_provider']}")
    print(f"  - Online Tools: {config['online_tools']}")
    print()
    
    try:
        # Test 1: Initialize TradingAgents with crypto config
        print("📊 Test 1: Initializing TradingAgents with crypto config...")
        ta = TradingAgentsGraph(
            selected_analysts=["market"],  # Start with just market analyst
            debug=False,  # No debug for integration test
            config=config
        )
        print("✅ TradingAgents initialized successfully!")
        print()
        
        # Test 2: Test crypto data fetching tools directly
        print("🔍 Test 2: Testing crypto tools directly...")
        toolkit = ta.toolkit
        
        btc_data = toolkit.get_crypto_data_online.invoke({"symbol": "BTC", "start_date": "2024-12-01", "end_date": "2024-12-07"})
        print(f"✅ BTC data fetch: {len(btc_data)} characters returned")
        
        btc_info = toolkit.get_crypto_info_online.invoke({"symbol": "BTC"})
        print(f"✅ BTC info fetch: {len(btc_info)} characters returned")
        print()
        
        # Test 3: Run a lightweight analysis (market analyst only)
        print("🤖 Test 3: Running lightweight crypto analysis...")
        print("  (Using BTC and market analyst only for speed)")
        
        # Run the analysis - this should trigger crypto tools
        state, decision = ta.propagate("BTC", "2024-12-01")
        
        print("🎉 Analysis Complete!")
        print("=" * 60)
        print(f"📋 Decision Summary:")
        print(f"  - Symbol: BTC")
        print(f"  - Decision Length: {len(decision)} characters")
        print(f"  - Contains 'BTC': {'BTC' in decision}")
        print(f"  - Contains 'crypto': {'crypto' in decision.lower()}")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        print(f"🔍 Error type: {type(e).__name__}")
        import traceback
        print(f"📍 Traceback: {traceback.format_exc()}")
        return False

def test_toggle_functionality():
    """Test that the crypto toggle works correctly."""
    print("\n🔄 Testing Crypto Toggle Functionality")
    print("=" * 50)
    
    try:
        # Test config toggle
        print("📊 Test: Config toggle...")
        config_disabled = DEFAULT_CONFIG.copy()
        config_disabled["use_crypto"] = False
        print(f"  - Crypto disabled config: {config_disabled['use_crypto']}")
        
        config_enabled = DEFAULT_CONFIG.copy()
        config_enabled["use_crypto"] = True
        print(f"  - Crypto enabled config: {config_enabled['use_crypto']}")
        
        # Test basic initialization with different configs
        print("📊 Test: TradingAgents initialization...")
        ta_disabled = TradingAgentsGraph(
            selected_analysts=["market"],
            debug=False,
            config=config_disabled
        )
        print(f"  ✅ Disabled mode initialized")
        
        ta_enabled = TradingAgentsGraph(
            selected_analysts=["market"],
            debug=False,
            config=config_enabled
        )
        print(f"  ✅ Enabled mode initialized")
        
        # Test that crypto tools are available in enabled mode
        try:
            crypto_result = ta_enabled.toolkit.get_crypto_data_online.invoke({"symbol": "BTC", "start_date": "2024-12-01", "end_date": "2024-12-02"})
            print(f"  ✅ Crypto tools accessible: {len(crypto_result)} chars returned")
        except Exception as e:
            print(f"  ❌ Crypto tools failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Toggle test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Starting Crypto Pipeline Integration Tests\n")
    
    # Run toggle test first
    toggle_success = test_toggle_functionality()
    
    # Run integration test
    integration_success = test_crypto_integration()
    
    print("\n📋 Test Results Summary:")
    print(f"  - Toggle functionality: {'✅ PASS' if toggle_success else '❌ FAIL'}")
    print(f"  - Integration test: {'✅ PASS' if integration_success else '❌ FAIL'}")
    
    if toggle_success and integration_success:
        print("\n🎉 All crypto pipeline tests passed!")
        print("🚀 Ready for crypto trading analysis!")
    else:
        print("\n⚠️  Some tests failed. Check the output above.") 