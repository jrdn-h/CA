from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

def test_trading_agents():
    print("🚀 Testing TradingAgents Framework")
    print("=" * 50)
    
    # Create a custom config for testing with cost-effective models
    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = "openai"
    config["deep_think_llm"] = "gpt-4o-mini"  # Using mini version to save costs
    config["quick_think_llm"] = "gpt-4o-mini"  # Using mini version to save costs
    config["max_debate_rounds"] = 1  # Keep it simple for testing
    config["online_tools"] = True  # Use real-time data
    
    print(f"📊 Configuration:")
    print(f"  - LLM Provider: {config['llm_provider']}")
    print(f"  - Deep Think LLM: {config['deep_think_llm']}")
    print(f"  - Quick Think LLM: {config['quick_think_llm']}")
    print(f"  - Backend URL: {config['backend_url']}")
    print(f"  - Online Tools: {config['online_tools']}")
    print(f"  - Max Debate Rounds: {config['max_debate_rounds']}")
    print()
    
    try:
        # Initialize the TradingAgents framework
        print("🔄 Initializing TradingAgents...")
        ta = TradingAgentsGraph(debug=True, config=config)
        print("✅ TradingAgents initialized successfully!")
        print()
        
        # Test with a popular stock
        ticker = "AAPL"  # Apple Inc.
        date = "2024-12-01"  # Recent date
        
        print(f"📈 Testing analysis for {ticker} on {date}")
        print("🤖 Starting multi-agent analysis...")
        print("   This may take a few minutes as agents analyze market data...")
        print()
        
        # Run the analysis
        state, decision = ta.propagate(ticker, date)
        
        print("🎉 Analysis Complete!")
        print("=" * 50)
        print(f"📋 Final Decision for {ticker}:")
        print(decision)
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")
        print(f"🔍 Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = test_trading_agents()
    if success:
        print("✨ Test completed successfully!")
    else:
        print("⚠️  Test failed. Please check your API keys and configuration.") 