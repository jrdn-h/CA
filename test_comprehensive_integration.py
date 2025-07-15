#!/usr/bin/env python3
"""
Comprehensive Integration Tests for TradingAgents Crypto Infrastructure

This test suite validates the complete end-to-end functionality of the crypto trading system,
focusing on integration logic that can be tested without requiring external API keys or services.

Priority: HIGH (as identified in CRYPTO_INFRASTRUCTURE_STATUS.md)
"""

import sys
import os
import asyncio
import time
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import datetime, timedelta
import json
import signal

# Add the project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.dataflows.ccxt_adapters import CCXTAdapters
from tradingagents.dataflows.crypto_cache import CryptoCacheManager
from tradingagents.dataflows.metric_registry import MetricRegistry


class TimeoutException(Exception):
    """Custom timeout exception."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutException("Operation timed out")


class ComprehensiveIntegrationTestSuite:
    """Comprehensive integration test suite for crypto trading infrastructure."""
    
    def __init__(self):
        """Initialize test suite with shared resources."""
        # Generate unique timestamp for this test run
        self.test_timestamp = int(time.time() * 1000)  # Include milliseconds for uniqueness
        
        self.test_config = DEFAULT_CONFIG.copy()
        self.test_config.update({
            "use_crypto": True,
            "llm_provider": "openai", 
            "deep_think_llm": "gpt-4o-mini",
            "quick_think_llm": "gpt-4o-mini",
            "max_debate_rounds": 1,  # Keep efficient for testing
            "online_tools": False,  # Disable online tools to avoid API dependencies
            "redis_caching": False,  # Disable Redis for testing
            "data_dir": f"./test_data_{self.test_timestamp}",  # Unique data dir for testing
            "enable_onchain": False  # Disable onchain to avoid API dependencies
        })
        
        self.test_results = {}
        self.performance_metrics = {}
        
    def log_test_result(self, test_name, success, duration, details=None):
        """Log test results for reporting."""
        self.test_results[test_name] = {
            "success": success,
            "duration": duration,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        
    def log_performance_metric(self, metric_name, value, unit="ms"):
        """Log performance metrics."""
        self.performance_metrics[metric_name] = {
            "value": value,
            "unit": unit,
            "timestamp": datetime.now().isoformat()
        }

    def get_unique_config(self, suffix=""):
        """Get a unique configuration for this specific test."""
        unique_config = self.test_config.copy()
        unique_config["data_dir"] = f"./test_data_{self.test_timestamp}_{suffix}_{int(time.time())}"
        return unique_config


class MultiAgentWorkflowTests(ComprehensiveIntegrationTestSuite):
    """Test complete multi-agent trading workflows with crypto data."""
    
    def test_framework_initialization(self):
        """Test that the framework can initialize with crypto configuration."""
        print("🚀 Testing Framework Initialization with Crypto Config")
        print("=" * 70)
        
        start_time = time.time()
        
        try:
            # Test basic framework initialization
            print("📊 Initializing trading framework with crypto config...")
            graph = TradingAgentsGraph(
                selected_analysts=["market", "fundamentals"],  # Core analysts only
                config=self.get_unique_config("framework_init"),
                debug=False
            )
            
            print(f"✅ Framework initialized successfully")
            print(f"📡 Available tool nodes: {list(graph.tool_nodes.keys())}")
            
            # Validate core components
            assert hasattr(graph, 'tool_nodes'), "Graph should have tool_nodes"
            assert hasattr(graph, 'toolkit'), "Graph should have toolkit"
            assert len(graph.tool_nodes) > 0, "Should have at least one tool node"
            
            # Test crypto mode detection
            config = graph.config
            assert config.get("use_crypto") == True, "Crypto mode should be enabled"
            
            duration = time.time() - start_time
            self.log_test_result("framework_initialization", True, duration, {
                "tool_nodes": list(graph.tool_nodes.keys()),
                "crypto_enabled": config.get("use_crypto")
            })
            
            print(f"✅ Framework Initialization Test PASSED in {duration:.2f}s")
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("framework_initialization", False, duration, {"error": str(e)})
            print(f"❌ Framework Initialization Test FAILED: {e}")
            return False
    
    def test_crypto_vs_stock_mode_switching(self):
        """Test configuration differences between crypto and stock modes."""
        print("\n🔄 Testing Crypto vs Stock Mode Configuration")
        print("=" * 70)
        
        start_time = time.time()
        
        try:
            # Test 1: Crypto mode config
            print("📊 Testing Crypto Mode Configuration...")
            crypto_config = self.get_unique_config("crypto_mode")
            crypto_config["use_crypto"] = True
            
            crypto_graph = TradingAgentsGraph(
                selected_analysts=["market"],
                config=crypto_config,
                debug=False
            )
            
            crypto_tools = set(crypto_graph.tool_nodes.keys())
            print(f"   🔧 Crypto mode tools: {crypto_tools}")
            
            # Test 2: Stock mode config  
            print("📈 Testing Stock Mode Configuration...")
            stock_config = self.get_unique_config("stock_mode")
            stock_config["use_crypto"] = False
            
            stock_graph = TradingAgentsGraph(
                selected_analysts=["market"],
                config=stock_config,
                debug=False
            )
            
            stock_tools = set(stock_graph.tool_nodes.keys())
            print(f"   🔧 Stock mode tools: {stock_tools}")
            
            # Validate toolkit differences
            assert crypto_graph.config.get("use_crypto") == True, "Crypto config should enable crypto"
            assert stock_graph.config.get("use_crypto") == False, "Stock config should disable crypto"
            
            # Both should have basic tools, but specifics may differ
            assert len(crypto_tools) > 0, "Crypto mode should have tools"
            assert len(stock_tools) > 0, "Stock mode should have tools"
            
            duration = time.time() - start_time
            self.log_test_result("crypto_vs_stock_mode", True, duration, {
                "crypto_tools": list(crypto_tools),
                "stock_tools": list(stock_tools),
                "tools_identical": crypto_tools == stock_tools
            })
            
            print(f"✅ Crypto vs Stock Mode Test PASSED in {duration:.2f}s")
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("crypto_vs_stock_mode", False, duration, {"error": str(e)})
            print(f"❌ Crypto vs Stock Mode Test FAILED: {e}")
            return False


class SystemComponentTests(ComprehensiveIntegrationTestSuite):
    """Test system components without requiring external APIs."""
    
    def test_component_initialization(self):
        """Test that all core components can initialize properly."""
        print("\n🔧 Testing Core Component Initialization")
        print("=" * 70)
        
        start_time = time.time()
        
        try:
            components_tested = []
            
            # Test 1: CCXT Adapters
            print("📊 Testing CCXT Adapters initialization...")
            try:
                adapters = CCXTAdapters()
                assert hasattr(adapters, '_exchange_clients'), "Should have exchange clients cache"
                assert hasattr(adapters, 'cache_manager'), "Should have cache manager"
                components_tested.append("ccxt_adapters")
                print("   ✅ CCXT Adapters initialized successfully")
            except Exception as e:
                print(f"   ⚠️  CCXT Adapters initialization issue: {e}")
            
            # Test 2: Cache Manager
            print("💾 Testing Cache Manager initialization...")
            try:
                cache_manager = CryptoCacheManager()
                assert hasattr(cache_manager, 'cache_enabled'), "Should have cache enabled flag"
                # Cache may be disabled due to no Redis, which is fine for testing
                components_tested.append("cache_manager")
                print(f"   ✅ Cache Manager initialized (enabled: {cache_manager.cache_enabled})")
            except Exception as e:
                print(f"   ⚠️  Cache Manager initialization issue: {e}")
            
            # Test 3: Metric Registry
            print("📈 Testing Metric Registry initialization...")
            try:
                registry = MetricRegistry()
                assert hasattr(registry, 'providers'), "Should have providers list"
                components_tested.append("metric_registry")
                print("   ✅ Metric Registry initialized successfully")
            except Exception as e:
                print(f"   ⚠️  Metric Registry initialization issue: {e}")
            
            # Validate at least some components work
            assert len(components_tested) >= 2, "At least 2 core components should initialize"
            
            duration = time.time() - start_time
            self.log_test_result("component_initialization", True, duration, {
                "components_tested": components_tested,
                "components_count": len(components_tested)
            })
            
            print(f"✅ Component Initialization Test PASSED in {duration:.2f}s")
            print(f"   📊 {len(components_tested)} components initialized successfully")
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("component_initialization", False, duration, {"error": str(e)})
            print(f"❌ Component Initialization Test FAILED: {e}")
            return False
    
    def test_cache_fallback_logic(self):
        """Test cache fallback behavior without requiring Redis."""
        print("\n🔄 Testing Cache Fallback Logic")
        print("=" * 70)
        
        start_time = time.time()
        
        try:
            # Test cache manager with no Redis connection
            print("📊 Testing cache operations without Redis...")
            cache_manager = CryptoCacheManager(redis_host="invalid_host", redis_port=9999)
            
            # Should initialize but be disabled
            assert not cache_manager.cache_enabled, "Cache should be disabled with invalid Redis"
            
            # Test set operation (should fail gracefully)
            set_result = cache_manager.set("test_endpoint", {"data": "test"}, params={"key": "test"})
            assert not set_result, "Set should return False when cache disabled"
            
            # Test get operation (should return None gracefully)
            get_result = cache_manager.get("test_endpoint", params={"key": "test"})
            assert get_result is None, "Get should return None when cache disabled"
            
            print("   ✅ Cache fallback behavior working correctly")
            
            duration = time.time() - start_time
            self.log_test_result("cache_fallback_logic", True, duration, {
                "cache_enabled": cache_manager.cache_enabled,
                "set_result": set_result,
                "get_result": get_result
            })
            
            print(f"✅ Cache Fallback Logic Test PASSED in {duration:.2f}s")
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("cache_fallback_logic", False, duration, {"error": str(e)})
            print(f"❌ Cache Fallback Logic Test FAILED: {e}")
            return False


class ConfigurationTests(ComprehensiveIntegrationTestSuite):
    """Test configuration and setup logic."""
    
    def test_configuration_validation(self):
        """Test that configuration is properly validated and applied."""
        print("\n⚙️ Testing Configuration Validation")
        print("=" * 70)
        
        start_time = time.time()
        
        try:
            # Test 1: Default configuration
            print("📊 Testing default configuration...")
            default_config = DEFAULT_CONFIG.copy()
            assert isinstance(default_config, dict), "Default config should be a dictionary"
            assert "llm_provider" in default_config, "Should have LLM provider"
            
            # Test 2: Crypto configuration override
            print("🔧 Testing crypto configuration override...")
            crypto_config = self.get_unique_config("config_test")
            crypto_config.update({
                "use_crypto": True,
                "online_tools": False,
                "redis_caching": False
            })
            
            # Validate configuration values
            assert crypto_config["use_crypto"] == True, "Crypto should be enabled"
            assert crypto_config["online_tools"] == False, "Online tools should be disabled for testing"
            assert crypto_config["redis_caching"] == False, "Redis should be disabled for testing"
            
            # Test 3: Configuration in practice
            print("🚀 Testing configuration with framework...")
            graph = TradingAgentsGraph(
                selected_analysts=["market"],
                config=crypto_config,
                debug=False
            )
            
            # Validate configuration was applied
            applied_config = graph.config
            assert applied_config.get("use_crypto") == True, "Crypto config should be applied"
            
            duration = time.time() - start_time
            self.log_test_result("configuration_validation", True, duration, {
                "default_config_keys": list(default_config.keys()),
                "crypto_config_applied": applied_config.get("use_crypto"),
                "online_tools_disabled": applied_config.get("online_tools") == False
            })
            
            print(f"✅ Configuration Validation Test PASSED in {duration:.2f}s")
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("configuration_validation", False, duration, {"error": str(e)})
            print(f"❌ Configuration Validation Test FAILED: {e}")
            return False


class PerformanceTests(ComprehensiveIntegrationTestSuite):
    """Test performance characteristics without heavy external dependencies."""
    
    def test_initialization_performance(self):
        """Test framework initialization performance."""
        print("\n⚡ Testing Initialization Performance")
        print("=" * 70)
        
        start_time = time.time()
        
        try:
            initialization_times = []
            
            # Test multiple initializations
            print("🚀 Testing multiple framework initializations...")
            for i in range(3):
                init_start = time.time()
                
                # Use unique config for each performance test
                perf_config = self.get_unique_config(f"perf_test_{i}")
                
                graph = TradingAgentsGraph(
                    selected_analysts=["market"],  # Single analyst for speed
                    config=perf_config,
                    debug=False
                )
                
                init_duration = time.time() - init_start
                initialization_times.append(init_duration)
                print(f"   ✅ Initialization {i+1}: {init_duration:.2f}s")
            
            # Analyze performance
            avg_time = sum(initialization_times) / len(initialization_times)
            max_time = max(initialization_times)
            
            # Performance thresholds (generous for testing environment)
            assert avg_time < 10, f"Average initialization should be under 10s, got {avg_time:.2f}s"
            assert max_time < 15, f"Maximum initialization should be under 15s, got {max_time:.2f}s"
            
            duration = time.time() - start_time
            self.log_performance_metric("avg_initialization_time", avg_time, "seconds")
            self.log_performance_metric("max_initialization_time", max_time, "seconds")
            
            self.log_test_result("initialization_performance", True, duration, {
                "initialization_times": initialization_times,
                "avg_time": avg_time,
                "max_time": max_time
            })
            
            print(f"✅ Initialization Performance Test PASSED in {duration:.2f}s")
            print(f"   📊 Average init time: {avg_time:.2f}s")
            print(f"   🏁 Maximum init time: {max_time:.2f}s")
            
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test_result("initialization_performance", False, duration, {"error": str(e)})
            print(f"❌ Initialization Performance Test FAILED: {e}")
            return False


def run_comprehensive_integration_tests():
    """Run all comprehensive integration tests."""
    print("🚀 COMPREHENSIVE CRYPTO INTEGRATION TEST SUITE")
    print("=" * 80)
    print("Testing crypto trading infrastructure integration without external dependencies")
    print("Priority: HIGH (as identified in CRYPTO_INFRASTRUCTURE_STATUS.md)")
    print("=" * 80)
    
    # Clean up any existing ChromaDB data directory to avoid conflicts
    try:
        import shutil
        import tempfile
        import os
        import glob
        
        print("🧹 Cleaning up previous test data...")
        
        # Clean up test data directories
        test_data_dirs = glob.glob("./test_data_*")
        for test_dir in test_data_dirs:
            if os.path.exists(test_dir):
                print(f"   🗑️  Removing test directory: {test_dir}")
                shutil.rmtree(test_dir, ignore_errors=True)
        
        # Clean up ChromaDB directories
        potential_paths = [
            "./chroma.db",
            "./data/chroma.db", 
            "./chroma_*",
            os.path.join(tempfile.gettempdir(), "chroma*"),
            "./.chroma",
            "./simple_test_data"
        ]
        
        for path_pattern in potential_paths:
            matching_paths = glob.glob(path_pattern)
            for path in matching_paths:
                if os.path.exists(path):
                    print(f"   🗑️  Removing ChromaDB data: {path}")
                    if os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
                    else:
                        os.remove(path)
        
        # Also try to clean any ChromaDB collections programmatically
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Use the same settings as the application code to avoid conflicts
            client_settings = Settings(allow_reset=True)
            chroma_client = chromadb.Client(client_settings)
            
            # Reset the database at the beginning of the test run
            chroma_client.reset()

            collections = chroma_client.list_collections()
            for collection in collections:
                print(f"   🗑️  Deleting ChromaDB collection: {collection.name}")
                chroma_client.delete_collection(collection.name)
        except Exception as e:
            print(f"   ℹ️  ChromaDB collection cleanup note: {e}")
        
        print("✅ ChromaDB cleanup completed")
    except Exception as e:
        print(f"ℹ️  ChromaDB cleanup note: {e}")
        
    # Add some delay to ensure cleanup is complete
    time.sleep(2)
    
    start_time = time.time()
    
    # Track overall results
    all_tests_passed = True
    test_categories = []
    
    try:
        # 1. Multi-Agent Workflow Tests
        print("\n🤖 CATEGORY 1: FRAMEWORK & WORKFLOW TESTS")
        workflow_tests = MultiAgentWorkflowTests()
        
        test_1a = workflow_tests.test_framework_initialization()
        test_1b = workflow_tests.test_crypto_vs_stock_mode_switching()
        
        category_1_passed = test_1a and test_1b
        test_categories.append(("Framework & Workflows", category_1_passed))
        all_tests_passed = all_tests_passed and category_1_passed
        
        # 2. System Component Tests
        print("\n🔧 CATEGORY 2: SYSTEM COMPONENT TESTS")
        component_tests = SystemComponentTests()
        
        test_2a = component_tests.test_component_initialization()
        test_2b = component_tests.test_cache_fallback_logic()
        
        category_2_passed = test_2a and test_2b
        test_categories.append(("System Components", category_2_passed))
        all_tests_passed = all_tests_passed and category_2_passed
        
        # 3. Configuration Tests
        print("\n⚙️ CATEGORY 3: CONFIGURATION TESTS")
        config_tests = ConfigurationTests()
        
        test_3a = config_tests.test_configuration_validation()
        
        category_3_passed = test_3a
        test_categories.append(("Configuration Management", category_3_passed))
        all_tests_passed = all_tests_passed and category_3_passed
        
        # 4. Performance Tests
        print("\n⚡ CATEGORY 4: PERFORMANCE TESTS")
        performance_tests = PerformanceTests()
        
        test_4a = performance_tests.test_initialization_performance()
        
        category_4_passed = test_4a
        test_categories.append(("Performance Characteristics", category_4_passed))
        all_tests_passed = all_tests_passed and category_4_passed
        
    except Exception as e:
        print(f"\n💥 CRITICAL TEST SUITE FAILURE: {e}")
        all_tests_passed = False
    
    # Generate comprehensive test report
    total_duration = time.time() - start_time
    
    print("\n" + "=" * 80)
    print("📋 COMPREHENSIVE INTEGRATION TEST REPORT")
    print("=" * 80)
    
    for category_name, passed in test_categories:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} | {category_name}")
    
    print(f"\n⏱️  Total Test Suite Duration: {total_duration:.2f} seconds")
    print(f"📊 Test Categories: {len([c for c in test_categories if c[1]])}/{len(test_categories)} passed")
    
    if all_tests_passed:
        print("\n🎉 ALL COMPREHENSIVE INTEGRATION TESTS PASSED!")
        print("\n✨ TradingAgents crypto infrastructure integration is working correctly!")
        print("\n📈 Validated:")
        print("   • Framework initialization with crypto configuration")
        print("   • Multi-mode switching (crypto ↔ stock)")
        print("   • Core component integration")
        print("   • Cache fallback mechanisms")
        print("   • Configuration management")
        print("   • Performance characteristics")
        print("\n🚀 System is ready for crypto trading workflows!")
    else:
        print("\n⚠️  SOME INTEGRATION TESTS FAILED")
        print("Review individual test results above for details.")
    
    print("=" * 80)
    
    return all_tests_passed


if __name__ == "__main__":
    success = run_comprehensive_integration_tests()
    if not success:
        sys.exit(1) 