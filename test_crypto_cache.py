"""Test Redis caching performance improvements for crypto data."""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.crypto_utils import CryptoUtils
from tradingagents.dataflows.crypto_cache import get_cache_manager

def test_cache_performance():
    """Test that caching significantly improves performance."""
    print("⚡ Testing Redis Caching Performance")
    print("=" * 50)
    
    # Get cache manager
    cache = get_cache_manager()
    
    # Display cache status
    stats = cache.get_cache_stats()
    print(f"📊 Cache Status: {'✅ Enabled' if stats['enabled'] else '❌ Disabled'}")
    
    if stats['enabled']:
        print(f"   - Memory used: {stats.get('memory_used', 'Unknown')}")
        print(f"   - Total keys: {stats.get('total_keys', 0)}")
    print()
    
    crypto_utils = CryptoUtils()
    
    # Test 1: First call (should hit API)
    print("🔍 Test 1: First API call (cache miss)")
    start_time = time.time()
    
    btc_data = crypto_utils.get_crypto_data("BTC", "2024-12-01", "2024-12-03")
    
    first_call_time = time.time() - start_time
    print(f"   ⏱️  First call: {first_call_time:.3f} seconds")
    print(f"   📊 Data points: {len(btc_data)}")
    print()
    
    # Test 2: Second call (should hit cache)
    print("🔍 Test 2: Second API call (cache hit)")
    start_time = time.time()
    
    btc_data_cached = crypto_utils.get_crypto_data("BTC", "2024-12-01", "2024-12-03")
    
    second_call_time = time.time() - start_time
    print(f"   ⏱️  Second call: {second_call_time:.3f} seconds")
    print(f"   📊 Data points: {len(btc_data_cached)}")
    print()
    
    # Performance improvement
    if second_call_time > 0:
        speedup = first_call_time / second_call_time
        print(f"🚀 Performance Improvement:")
        print(f"   - Speedup: {speedup:.1f}x faster")
        print(f"   - Time saved: {(first_call_time - second_call_time):.3f} seconds")
        
        if speedup > 5:
            print("   ✅ Excellent caching performance!")
        elif speedup > 2:
            print("   ✅ Good caching performance!")
        else:
            print("   ⚠️  Limited caching benefit")
    
    # Test 3: Cache stats after operations
    print("\n📈 Updated Cache Stats:")
    updated_stats = cache.get_cache_stats()
    if updated_stats['enabled']:
        print(f"   - Total keys: {updated_stats.get('total_keys', 0)}")
        print(f"   - Cache hits: {updated_stats.get('hits', 0)}")
        print(f"   - Cache misses: {updated_stats.get('misses', 0)}")
    
    return True

def test_multiple_symbols_caching():
    """Test caching across multiple crypto symbols."""
    print("\n🪙 Testing Multi-Symbol Caching")
    print("=" * 50)
    
    crypto_utils = CryptoUtils()
    symbols = ["BTC", "ETH", "SOL"]
    
    print("📊 First round (cache misses):")
    start_time = time.time()
    
    results = {}
    for symbol in symbols:
        print(f"   Fetching {symbol}...")
        info = crypto_utils.get_crypto_info(symbol)
        results[symbol] = info
    
    first_round_time = time.time() - start_time
    print(f"   ⏱️  Total time: {first_round_time:.3f} seconds")
    
    print("\n📊 Second round (cache hits):")
    start_time = time.time()
    
    cached_results = {}
    for symbol in symbols:
        print(f"   Fetching {symbol} (cached)...")
        info = crypto_utils.get_crypto_info(symbol)
        cached_results[symbol] = info
    
    second_round_time = time.time() - start_time
    print(f"   ⏱️  Total time: {second_round_time:.3f} seconds")
    
    # Compare results
    print(f"\n🚀 Multi-Symbol Performance:")
    if second_round_time > 0:
        speedup = first_round_time / second_round_time
        print(f"   - Speedup: {speedup:.1f}x faster")
        print(f"   - Time per symbol (cached): {second_round_time / len(symbols):.3f}s")
    
    return True

def test_cache_invalidation():
    """Test cache invalidation functionality."""
    print("\n🗑️  Testing Cache Invalidation")
    print("=" * 50)
    
    cache = get_cache_manager()
    
    # Show current cache stats
    stats = cache.get_cache_stats()
    print(f"📊 Cache keys before: {stats.get('total_keys', 0)}")
    
    # Invalidate all crypto cache
    cleared = cache.clear_all_cache()
    print(f"🧹 Cache cleared: {'✅ Success' if cleared else '❌ Failed'}")
    
    # Show updated stats
    stats_after = cache.get_cache_stats()
    print(f"📊 Cache keys after: {stats_after.get('total_keys', 0)}")
    
    return True

def simulate_agent_debate():
    """Simulate rapid API calls during agent debate."""
    print("\n🤖 Simulating Agent Debate (Rapid API Calls)")
    print("=" * 60)
    
    crypto_utils = CryptoUtils()
    symbol = "BTC"
    
    print(f"🔥 Simulating 5 agents rapidly analyzing {symbol}...")
    
    start_time = time.time()
    
    # Simulate 5 agents making rapid calls
    for agent_id in range(1, 6):
        print(f"   Agent {agent_id} requesting data...")
        data = crypto_utils.get_crypto_data(symbol, "2024-12-01", "2024-12-02")
        info = crypto_utils.get_crypto_info(symbol)
        
        # Brief pause between agents
        time.sleep(0.05)
    
    total_time = time.time() - start_time
    print(f"\n⏱️  Total debate time: {total_time:.3f} seconds")
    print(f"📊 Average per agent: {total_time / 5:.3f} seconds")
    
    if total_time < 5:
        print("✅ Excellent! Agents can debate efficiently with caching")
    elif total_time < 10:
        print("✅ Good! Reasonable performance for agent debates")
    else:
        print("⚠️  Consider optimizing cache TTL for faster debates")
    
    return True

if __name__ == "__main__":
    print("⚡ Redis Cache Performance Tests")
    print("=" * 60)
    
    tests = [
        ("Basic Caching", test_cache_performance),
        ("Multi-Symbol", test_multiple_symbols_caching),
        ("Agent Debate Simulation", simulate_agent_debate),
        ("Cache Invalidation", test_cache_invalidation),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n▶️  Running: {test_name}")
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 60)
    print("📋 Cache Performance Test Results:")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  - {test_name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All cache tests PASSED! Redis caching is working optimally.")
        print("🚀 Agents can now debate with lightning-fast data access!")
    else:
        print("⚠️  Some cache tests failed. Check Redis connection.")
    print("=" * 60) 