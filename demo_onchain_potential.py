"""Demo: On-Chain Analytics Potential with Mock Data"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
from datetime import datetime, timedelta

def create_mock_onchain_analysis():
    """Create mock on-chain analysis to demonstrate potential."""
    
    # Simulate what real Glassnode data would provide
    mock_analysis = {
        "BTC": {
            "asset": "BTC",
            "timestamp": datetime.now().isoformat(),
            "data_sources": ["Glassnode", "IntoTheBlock"],
            "network_health": {
                "health_score": "Excellent",
                "avg_daily_transactions": 267845,
                "hash_rate_th": "275.2",
                "active_addresses": 982341,
                "address_trend": "increasing"
            },
            "market_indicators": {
                "market_cap_usd": "$2,156,780,000,000",
                "price_usd": "$116,428.00",
                "price_change_7d_pct": "+3.45%",
                "nvt_ratio": "52.3",
                "mvrv_ratio": "1.85"
            },
            "address_metrics": {
                "current_active_addresses": 982341,
                "30d_average": 943212,
                "trend": "increasing",
                "data_points": 30,
                "timeframe": "2024-12-15 to 2025-01-15"
            },
            "advanced_metrics": {
                "hodl_waves": {
                    "1d_to_1w": "2.3%",
                    "1w_to_1m": "8.7%", 
                    "1m_to_3m": "15.2%",
                    "3m_to_6m": "12.8%",
                    "6m_to_1y": "18.4%",
                    "1y_to_2y": "16.9%",
                    "2y_plus": "25.7%"
                },
                "exchange_flows": {
                    "net_flow_7d": "-12,450 BTC",
                    "trend": "outflow",
                    "signal": "bullish"
                },
                "whale_activity": {
                    "large_transactions_24h": 1247,
                    "whale_accumulation": "increasing",
                    "top_100_balance": "14.2% of supply"
                }
            },
            "summary": """
BTC On-Chain Analysis Summary:
- Network Health: Excellent
- Daily Transactions: 267,845
- Address Activity: increasing  
- Current Active Addresses: 982,341
- Exchange Outflows: Strong (-12,450 BTC/7d)
- Whale Accumulation: Increasing
- Long-term Holders: 61% (1y+)
            """.strip()
        },
        "ETH": {
            "asset": "ETH", 
            "timestamp": datetime.now().isoformat(),
            "data_sources": ["Glassnode", "Dune Analytics"],
            "network_health": {
                "health_score": "Good",
                "avg_daily_transactions": 1156789,
                "gas_usage_avg": "85.6%",
                "active_addresses": 567234,
                "address_trend": "stable"
            },
            "defi_metrics": {
                "total_value_locked": "$45,600,000,000",
                "staking_ratio": "28.3%",
                "burn_rate_7d": "3,456 ETH",
                "net_issuance": "-0.45% (deflationary)"
            },
            "market_indicators": {
                "market_cap_usd": "$515,780,000,000", 
                "price_usd": "$4,289.50",
                "price_change_7d_pct": "+1.23%",
                "eth_btc_ratio": "0.0368"
            },
            "summary": """
ETH On-Chain Analysis Summary:
- Network Health: Good
- Daily Transactions: 1,156,789
- DeFi TVL: $45.6B (+2.1% weekly)
- Staking: 28.3% of supply
- Deflationary: -0.45% issuance
- Gas Usage: 85.6% (high demand)
            """.strip()
        }
    }
    
    return mock_analysis

def demo_ai_agent_insights():
    """Demonstrate rich insights for AI agent consumption."""
    print("🤖 Demo: AI Agent On-Chain Intelligence")
    print("=" * 60)
    
    mock_data = create_mock_onchain_analysis()
    
    for asset, analysis in mock_data.items():
        print(f"\n🔍 {asset} On-Chain Intelligence")
        print("-" * 40)
        
        # Extract actionable signals for AI
        signals = []
        
        # Network health signals
        health = analysis["network_health"]["health_score"]
        if health == "Excellent":
            signals.append("Strong network fundamentals")
        elif health == "Good":
            signals.append("Stable network activity")
        
        # Address activity signals
        address_trend = analysis["network_health"]["address_trend"] 
        if address_trend == "increasing":
            signals.append("Growing user adoption")
        elif address_trend == "stable":
            signals.append("Stable user base")
        
        # Advanced signals (if available)
        if "advanced_metrics" in analysis:
            exchange_trend = analysis["advanced_metrics"]["exchange_flows"]["trend"]
            if exchange_trend == "outflow":
                signals.append("Exchange outflows (supply squeeze)")
            
            whale_activity = analysis["advanced_metrics"]["whale_activity"]["whale_accumulation"]
            if whale_activity == "increasing":
                signals.append("Whale accumulation pattern")
        
        # DeFi signals (for ETH)
        if "defi_metrics" in analysis:
            if "deflationary" in analysis["defi_metrics"]["net_issuance"]:
                signals.append("Deflationary token economics")
        
        print("📊 Key Signals for AI:")
        for signal in signals:
            print(f"   • {signal}")
        
        print(f"\n💡 AI Investment Thesis:")
        if asset == "BTC":
            thesis = """
Based on on-chain data:
• Network security at ATH (hash rate)
• Accumulation phase (exchange outflows) 
• Long-term holder dominance (61%)
• Institutional adoption signals
→ Fundamental strength supporting price
            """.strip()
        else:  # ETH
            thesis = """
Based on on-chain data:
• High network utilization (85% gas)
• Deflationary mechanics active
• Strong DeFi ecosystem ($45B TVL)
• Proof-of-stake security model
→ Utility-driven value proposition
            """.strip()
        
        print(thesis)
        print("-" * 40)

def demo_multi_asset_comparison():
    """Demo multi-asset on-chain comparison."""
    print("\n📊 Multi-Asset On-Chain Comparison")
    print("=" * 60)
    
    mock_data = create_mock_onchain_analysis()
    
    # Create comparison matrix
    comparison = {
        "Network Health": {
            "BTC": mock_data["BTC"]["network_health"]["health_score"],
            "ETH": mock_data["ETH"]["network_health"]["health_score"]
        },
        "Daily Transactions": {
            "BTC": f"{mock_data['BTC']['network_health']['avg_daily_transactions']:,}",
            "ETH": f"{mock_data['ETH']['network_health']['avg_daily_transactions']:,}"
        },
        "Address Trend": {
            "BTC": mock_data["BTC"]["network_health"]["address_trend"],
            "ETH": mock_data["ETH"]["network_health"]["address_trend"]
        },
        "Key Strength": {
            "BTC": "Store of Value",
            "ETH": "DeFi Ecosystem"
        }
    }
    
    print("🔍 Cross-Asset Analysis:")
    for metric, assets in comparison.items():
        print(f"\n📈 {metric}:")
        for asset, value in assets.items():
            print(f"   {asset}: {value}")
    
    print(f"\n🎯 Portfolio Insights:")
    print("   • BTC: Macro store-of-value play")
    print("   • ETH: Ecosystem utility token")
    print("   • Complementary exposure")
    print("   • Risk diversification")

def demo_agent_decision_support():
    """Demo how on-chain data supports agent decisions."""
    print("\n🧠 AI Agent Decision Support")
    print("=" * 60)
    
    mock_data = create_mock_onchain_analysis()
    btc_data = mock_data["BTC"]
    
    # Simulate agent decision process
    decision_factors = []
    confidence_score = 0
    
    # Factor 1: Network health
    health = btc_data["network_health"]["health_score"]
    if health == "Excellent":
        decision_factors.append("✅ Excellent network health (+20)")
        confidence_score += 20
    
    # Factor 2: Address activity
    if btc_data["network_health"]["address_trend"] == "increasing":
        decision_factors.append("✅ Growing user adoption (+15)")
        confidence_score += 15
    
    # Factor 3: Exchange flows
    if "outflow" in btc_data["advanced_metrics"]["exchange_flows"]["trend"]:
        decision_factors.append("✅ Exchange outflows (+25)")
        confidence_score += 25
    
    # Factor 4: Whale activity
    if btc_data["advanced_metrics"]["whale_activity"]["whale_accumulation"] == "increasing":
        decision_factors.append("✅ Whale accumulation (+15)")
        confidence_score += 15
    
    # Factor 5: Long-term holders
    hodl_2y_plus = float(btc_data["advanced_metrics"]["hodl_waves"]["2y_plus"].rstrip('%'))
    if hodl_2y_plus > 20:
        decision_factors.append(f"✅ Strong HODLer base ({hodl_2y_plus}%) (+10)")
        confidence_score += 10
    
    print("🔍 Agent Decision Process:")
    for factor in decision_factors:
        print(f"   {factor}")
    
    print(f"\n📊 Confidence Score: {confidence_score}/100")
    
    if confidence_score >= 70:
        recommendation = "STRONG BUY"
        color = "🟢"
    elif confidence_score >= 50:
        recommendation = "BUY"  
        color = "🟡"
    else:
        recommendation = "HOLD"
        color = "🔴"
    
    print(f"\n{color} AI Recommendation: {recommendation}")
    print(f"💡 Reasoning: On-chain fundamentals strongly support bullish thesis")

if __name__ == "__main__":
    print("🔗 On-Chain Analytics: Full Potential Demo")
    print("=" * 70)
    
    demo_ai_agent_insights()
    demo_multi_asset_comparison()
    demo_agent_decision_support()
    
    print("\n" + "=" * 70)
    print("🎯 On-Chain Analytics Impact:")
    print("=" * 70)
    print("✅ Deep fundamental analysis beyond price")
    print("✅ Early detection of trend reversals")
    print("✅ Whale/institutional activity tracking")
    print("✅ Network health monitoring")
    print("✅ Multi-timeframe insights")
    print("✅ Quantified confidence scoring")
    print("✅ Cross-asset comparison")
    print("✅ AI agent decision support")
    print("\n🚀 Ready to give agents blockchain superpowers!")
    print("=" * 70) 