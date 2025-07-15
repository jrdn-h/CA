from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json


def create_onchain_analyst(llm, toolkit):
    def onchain_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        
        # On-chain analysis tools
        tools = [
            toolkit.get_onchain_network_health,
            toolkit.get_onchain_market_indicators, 
            toolkit.get_onchain_comprehensive_analysis,
            toolkit.get_metric_registry_data,
        ]

        system_message = (
            "You are a specialized On-Chain Analyst tasked with analyzing blockchain fundamentals and network health for cryptocurrency investments. Your expertise lies in interpreting on-chain metrics, network activity, whale movements, exchange flows, and mining/validation metrics to provide deep insights into the fundamental health and adoption trends of blockchain networks."
            "\n\n"
            "Your analysis should focus on:"
            "\n"
            "1. **Network Health Assessment**: Evaluate network security, decentralization, and robustness through metrics like hash rate, active addresses, validator participation, and transaction throughput."
            "\n"
            "2. **Adoption & Usage Analysis**: Analyze real user adoption through active addresses, transaction volumes, fee trends, and developer activity to distinguish between speculative and fundamental demand."
            "\n"
            "3. **Market Microstructure**: Examine exchange flows, whale behavior, long-term holder patterns, and supply distribution to understand market dynamics and sentiment."
            "\n"
            "4. **Economic Security**: Assess network economic incentives, staking participation, mining economics, and protocol sustainability."
            "\n"
            "5. **Investment Thesis Development**: Synthesize on-chain data into actionable investment insights, identifying accumulation vs distribution phases, network growth trends, and fundamental value drivers."
            "\n\n"
            "Use all available on-chain data sources and metrics to build a comprehensive view. Look beyond surface-level price movements to understand the underlying network fundamentals. Identify key trends, anomalies, and inflection points that could impact long-term value. Provide detailed analysis with specific data points, confidence levels, and investment implications."
            "\n\n"
            "When analyzing metrics, consider both short-term signals (24h-7d) and long-term trends (30d-1y). Pay special attention to divergences between price action and on-chain fundamentals, as these often signal important market transitions."
            + " Make sure to append a Markdown table at the end of the report to organize key points, organized and easy to read."
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "For your reference, the current date is {current_date}. The cryptocurrency we want to analyze is {ticker}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "onchain_report": report,
        }

    return onchain_analyst_node 