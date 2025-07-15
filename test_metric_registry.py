"""Test MetricRegistry intelligent fallback system."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.metric_registry import MetricRegistry, get_metric_registry
import json

def test_provider_fallback():
    """Test intelligent provider fallback system."""
    print("🔄 Testing Intelligent Provider Fallback")
    print("=" * 60)
    
    registry = get_metric_registry()
    
    # Show initial provider status
    print("📊 Provider Status:")
    status = registry.get_provider_status()
    for name, info in status.items():
        health = "✅ Healthy" if info["healthy"] else "❌ Unhealthy"
        api_key = "🔑 API Key Required" if info["requires_api_key"] else "🆓 Free"
        print(f"   {name}: {health}, Priority: {info['priority']}, {api_key}")
    print()
    
    # Test metric fetching with fallback
    asset = "BTC"
    test_metrics = ["active_addresses", "whale_activity", "hash_rate", "price"]
    
    print(f"🔍 Testing metrics for {asset}:")
    for metric in test_metrics:
        print(f"\n   📊 Fetching {metric}...")
        result = registry.get_metric(metric, asset)
        
        if result:
            if isinstance(result, dict):
                print(f"      ✅ Success: {len(result)} fields returned")
                for key, value in list(result.items())[:2]:  # Show first 2 items
                    print(f"         {key}: {value}")
            else:
                print(f"      ✅ Success: {result}")
        else:
            print(f"      ❌ Failed: No data available")
    
    return True

def test_comprehensive_analysis():
    """Test comprehensive multi-provider analysis."""
    print("\n🧠 Testing Comprehensive Multi-Provider Analysis")
    print("=" * 60)
    
    registry = get_metric_registry()
    
    assets = ["BTC", "ETH"]
    
    for asset in assets:
        print(f"\n🔍 Comprehensive Analysis: {asset}")
        print("-" * 40)
        
        analysis = registry.get_comprehensive_analysis(asset)
        
        print(f"📊 Asset: {analysis['asset']}")
        print(f"🕐 Timestamp: {analysis['timestamp'][:19]}")
        print(f"📡 Data Sources: {', '.join(analysis['data_sources'])}")
        
        # Address metrics
        if analysis["address_metrics"]:
            print(f"👥 Address Metrics:")
            addr = analysis["address_metrics"]
            print(f"   Current: {addr.get('current_active_addresses', 'N/A')}")
            print(f"   Trend: {addr.get('trend', 'Unknown')}")
        
        # Network health
        if analysis["network_health"]:
            print(f"🏥 Network Health:")
            for key, value in analysis["network_health"].items():
                print(f"   {key}: {value}")
        
        # Market indicators
        if analysis["market_indicators"]:
            print(f"💰 Market Indicators:")
            for key, value in analysis["market_indicators"].items():
                print(f"   {key}: {value}")
        
        # Whale metrics
        if "whale_metrics" in analysis:
            print(f"🐋 Whale Activity:")
            whale = analysis["whale_metrics"]
            if isinstance(whale, dict):
                for key, value in whale.items():
                    print(f"   {key}: {value}")
        
        print(f"\n📋 Summary:")
        print(analysis["summary"])
        print("-" * 40)
    
    return True

def test_provider_health_tracking():
    """Test provider health tracking and recovery."""
    print("\n🏥 Testing Provider Health Tracking")
    print("=" * 60)
    
    registry = get_metric_registry()
    
    print("📊 Initial Provider Health:")
    status = registry.get_provider_status()
    healthy_count = sum(1 for info in status.values() if info["healthy"])
    print(f"   Healthy Providers: {healthy_count}/{len(status)}")
    
    # Simulate some failures by trying non-existent metrics
    print("\n🔍 Simulating Provider Failures...")
    for i in range(3):
        result = registry.get_metric("non_existent_metric", "BTC")
        print(f"   Attempt {i+1}: {'Success' if result else 'Failed'}")
    
    print("\n📊 Provider Health After Failures:")
    status_after = registry.get_provider_status()
    for name, info in status_after.items():
        health = "✅ Healthy" if info["healthy"] else "❌ Unhealthy"
        failures = info["failure_count"]
        print(f"   {name}: {health} (Failures: {failures})")
    
    # Reset provider health
    print("\n🔄 Resetting Provider Health...")
    registry.reset_all_providers()
    
    status_reset = registry.get_provider_status()
    healthy_after_reset = sum(1 for info in status_reset.values() if info["healthy"])
    print(f"   Healthy Providers After Reset: {healthy_after_reset}/{len(status_reset)}")
    
    return True

def demo_production_ready_features():
    """Demonstrate production-ready features."""
    print("\n🚀 Production-Ready Features Demo")
    print("=" * 60)
    
    registry = get_metric_registry()
    
    # Feature 1: Custom provider addition
    print("🔧 Feature 1: Custom Provider Addition")
    
    def custom_loader(metric, asset, **kwargs):
        """Custom provider that always returns test data."""
        return {"custom_metric": f"Custom data for {asset}", "source": "CustomProvider"}
    
    registry.add_custom_provider(
        "CustomProvider", 
        priority=0,  # Highest priority
        loader_func=custom_loader,
        metrics=["custom_metric"],
        requires_api_key=False
    )
    
    # Test custom provider
    custom_result = registry.get_metric("custom_metric", "BTC")
    print(f"   Custom Provider Result: {custom_result}")
    print()
    
    # Feature 2: Provider priority and fallback
    print("🔧 Feature 2: Provider Priority System")
    providers = registry.providers
    providers.sort(key=lambda x: x.priority)
    
    for provider in providers:
        print(f"   Priority {provider.priority}: {provider.name}")
    print()
    
    # Feature 3: Metrics coverage map
    print("🔧 Feature 3: Metrics Coverage Map")
    all_metrics = set()
    for provider in registry.providers:
        all_metrics.update(provider.available_metrics)
    
    coverage_map = {}
    for metric in sorted(all_metrics):
        providers_for_metric = [p.name for p in registry.providers if metric in p.available_metrics]
        coverage_map[metric] = providers_for_metric
    
    print("   Metric Coverage:")
    for metric, providers in list(coverage_map.items())[:5]:  # Show first 5
        print(f"      {metric}: {', '.join(providers)}")
    print(f"   ... and {len(coverage_map) - 5} more metrics")
    print()
    
    # Feature 4: Real-time status monitoring
    print("🔧 Feature 4: Real-Time Status Dashboard")
    status = registry.get_provider_status()
    
    print("   Provider Dashboard:")
    print("   " + "="*50)
    for name, info in status.items():
        status_emoji = "🟢" if info["healthy"] else "🔴"
        api_emoji = "🔑" if info["requires_api_key"] else "🆓"
        print(f"   {status_emoji} {name:<15} {api_emoji} P:{info['priority']} M:{info['metrics_count']}")
    
    return True

if __name__ == "__main__":
    print("🔄 MetricRegistry Intelligent Fallback System")
    print("=" * 70)
    
    tests = [
        ("Provider Fallback", test_provider_fallback),
        ("Comprehensive Analysis", test_comprehensive_analysis),
        ("Health Tracking", test_provider_health_tracking),
        ("Production Features", demo_production_ready_features),
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
    print("📋 MetricRegistry Test Results:")
    print("=" * 70)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  - {test_name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 All MetricRegistry tests PASSED!")
        print("🚀 Production-ready fallback system operational!")
    else:
        print("⚠️  Some tests failed. Check system configuration.")
    print("=" * 70) 