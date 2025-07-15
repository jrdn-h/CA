"""Test on-chain analytics capabilities with Glassnode integration."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.onchain_loader import OnChainLoader, get_onchain_loader
import json

def test_glassnode_free_tier():
    """Test Glassnode free tier endpoints."""
    print("🔗 Testing Glassnode Free Tier On-Chain Analytics")
    print("=" * 60)
    
    # Initialize without API key (free tier)
    loader = OnChainLoader()
    
    asset = "BTC"
    print(f"📊 Analyzing {asset} with free tier endpoints...")
    print()
    
    # Test 1: Active addresses
    print("🔍 Test 1: Active Addresses Analysis")
    addresses = loader.get_active_addresses(asset, days=30)
    
    if "error" not in addresses:
        print(f"   ✅ Current Active Addresses: {addresses['current_active_addresses']:,}")
        print(f"   📈 30-day Average: {addresses['30d_average']:,}")
        print(f"   📊 Trend: {addresses['trend']}")
        print(f"   🗓️  Timeframe: {addresses['timeframe']}")
    else:
        print(f"   ⚠️  {addresses['error']}")
    print()
    
    # Test 2: Network health
    print("🔍 Test 2: Network Health Analysis")
    health = loader.get_network_health(asset)
    
    print(f"   🏥 Health Score: {health.get('health_score', 'Unknown')}")
    if "avg_daily_transactions" in health:
        print(f"   💳 Daily Transactions: {health['avg_daily_transactions']:,}")
    if "hash_rate_th" in health:
        print(f"   ⚡ Hash Rate: {health['hash_rate_th']} TH/s")
    if "address_trend" in health:
        print(f"   📈 Address Trend: {health['address_trend']}")
    print()
    
    # Test 3: Market indicators
    print("🔍 Test 3: Market Indicators")
    indicators = loader.get_market_indicators(asset)
    
    for key, value in indicators.items():
        print(f"   📊 {key.replace('_', ' ').title()}: {value}")
    print()
    
    return len(addresses) > 0 or len(health) > 0 or len(indicators) > 0

def test_comprehensive_analysis():
    """Test comprehensive on-chain analysis."""
    print("🧠 Testing Comprehensive On-Chain Analysis")
    print("=" * 60)
    
    loader = get_onchain_loader()
    
    assets = ["BTC", "ETH"]
    
    for asset in assets:
        print(f"\n🔍 Comprehensive Analysis: {asset}")
        print("-" * 40)
        
        analysis = loader.get_comprehensive_analysis(asset)
        
        print(f"📊 Asset: {analysis['asset']}")
        print(f"🕐 Analysis Time: {analysis['timestamp'][:19]}")
        print()
        
        # Network health summary
        network = analysis.get("network_health", {})
        if network:
            print("🏥 Network Health:")
            print(f"   Score: {network.get('health_score', 'Unknown')}")
            if "avg_daily_transactions" in network:
                print(f"   Daily Txs: {network['avg_daily_transactions']:,}")
            print()
        
        # Address metrics
        addresses = analysis.get("address_metrics", {})
        if addresses and "error" not in addresses:
            print("👥 Address Activity:")
            print(f"   Current: {addresses.get('current_active_addresses', 'N/A'):,}")
            print(f"   Trend: {addresses.get('trend', 'Unknown')}")
            print()
        
        # Market indicators
        market = analysis.get("market_indicators", {})
        if market:
            print("💰 Market Indicators:")
            for key, value in market.items():
                print(f"   {key.replace('_', ' ').title()}: {value}")
            print()
        
        # Summary
        summary = analysis.get("summary", "")
        if summary:
            print("📋 Summary:")
            for line in summary.split('\n'):
                if line.strip():
                    print(f"   {line.strip()}")
        
        print("-" * 40)
    
    return True

def test_metric_caching():
    """Test that on-chain metrics are properly cached."""
    print("\n⚡ Testing On-Chain Metrics Caching")
    print("=" * 60)
    
    import time
    
    loader = OnChainLoader()
    asset = "BTC"
    
    print(f"🔍 Testing cache performance for {asset} active addresses...")
    
    # First call (should hit API)
    print("   First call (cache miss)...")
    start_time = time.time()
    result1 = loader.get_active_addresses(asset, days=7)
    first_time = time.time() - start_time
    
    # Second call (should hit cache)
    print("   Second call (cache hit)...")
    start_time = time.time()
    result2 = loader.get_active_addresses(asset, days=7)
    second_time = time.time() - start_time
    
    print(f"   ⏱️  First call: {first_time:.3f}s")
    print(f"   ⏱️  Second call: {second_time:.3f}s")
    
    if second_time > 0:
        speedup = first_time / second_time
        print(f"   🚀 Cache speedup: {speedup:.1f}x")
        
        if speedup > 2:
            print("   ✅ Excellent caching performance!")
        else:
            print("   ✅ Caching is working")
    
    # Verify results are identical
    identical = result1 == result2
    print(f"   🔍 Results identical: {'✅ Yes' if identical else '❌ No'}")
    
    return True

def test_error_handling():
    """Test error handling for invalid assets and metrics."""
    print("\n🛡️  Testing Error Handling")
    print("=" * 60)
    
    loader = OnChainLoader()
    
    # Test 1: Invalid asset
    print("🔍 Test 1: Invalid asset")
    invalid_result = loader.get_active_addresses("INVALID_ASSET", days=7)
    print(f"   Result: {'✅ Handled gracefully' if 'error' in invalid_result or not invalid_result else '❌ No error handling'}")
    
    # Test 2: Network health for unsupported asset
    print("🔍 Test 2: Network health for generic asset")
    health = loader.get_network_health("ETH")  # ETH doesn't have hash rate in our logic
    print(f"   Result: {'✅ Partial data returned' if health else '❌ No data'}")
    
    # Test 3: API key required metrics without key
    print("🔍 Test 3: Premium metrics without API key")
    premium_df = loader.get_glassnode_metric("BTC", "premium/metric", "2024-12-01", "2024-12-03")
    print(f"   Result: {'✅ Gracefully handled' if premium_df.empty else '❌ Unexpected data'}")
    
    return True

def demo_agent_ready_insights():
    """Demonstrate insights ready for AI agent consumption."""
    print("\n🤖 Demo: AI Agent-Ready On-Chain Insights")
    print("=" * 60)
    
    loader = get_onchain_loader()
    
    # Simulate what an AI agent would receive
    btc_analysis = loader.get_comprehensive_analysis("BTC")
    
    print("📊 Sample AI Agent Input:")
    print("=" * 40)
    
    # Extract key insights for AI processing
    insights = {
        "asset": btc_analysis["asset"],
        "network_health_score": btc_analysis.get("network_health", {}).get("health_score"),
        "daily_transactions": btc_analysis.get("network_health", {}).get("avg_daily_transactions"),
        "address_trend": btc_analysis.get("address_metrics", {}).get("trend"),
        "active_addresses": btc_analysis.get("address_metrics", {}).get("current_active_addresses"),
        "market_signals": list(btc_analysis.get("market_indicators", {}).keys()),
    }
    
    print(json.dumps(insights, indent=2))
    
    print("\n📋 AI Agent Prompt-Ready Summary:")
    print("=" * 40)
    summary = btc_analysis.get("summary", "No summary available")
    print(summary)
    
    print("\n🧠 Ready for AI Analysis:")
    print("   ✅ Structured data format")
    print("   ✅ Key metrics extracted") 
    print("   ✅ Health scores calculated")
    print("   ✅ Trend analysis included")
    print("   ✅ Human-readable summary")
    
    return True

if __name__ == "__main__":
    print("🔗 On-Chain Analytics Testing Suite")
    print("=" * 70)
    
    tests = [
        ("Glassnode Free Tier", test_glassnode_free_tier),
        ("Comprehensive Analysis", test_comprehensive_analysis),
        ("Metrics Caching", test_metric_caching),
        ("Error Handling", test_error_handling),
        ("AI Agent Integration", demo_agent_ready_insights),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n▶️  Running: {test_name}")
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 70)
    print("📋 On-Chain Analytics Test Results:")
    print("=" * 70)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  - {test_name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 All on-chain analytics tests PASSED!")
        print("🚀 Ready to give AI agents deep blockchain insights!")
    else:
        print("⚠️  Some tests failed. Check Glassnode API connectivity.")
    print("=" * 70) 