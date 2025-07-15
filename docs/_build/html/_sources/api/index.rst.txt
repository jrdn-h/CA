API Reference
=============

This section contains the complete API reference for TradingAgents.

Core Modules
------------

.. autosummary::
   :toctree: generated
   :recursive:

   tradingagents.agents
   tradingagents.dataflows
   tradingagents.graph

Agents
------

.. autosummary::
   :toctree: generated

   tradingagents.agents.analysts.fundamentals_analyst
   tradingagents.agents.analysts.market_analyst
   tradingagents.agents.analysts.news_analyst
   tradingagents.agents.analysts.onchain_analyst
   tradingagents.agents.analysts.social_media_analyst
   tradingagents.agents.managers.research_manager
   tradingagents.agents.managers.risk_manager
   tradingagents.agents.researchers.bear_researcher
   tradingagents.agents.researchers.bull_researcher
   tradingagents.agents.risk_mgmt.aggresive_debator
   tradingagents.agents.risk_mgmt.conservative_debator
   tradingagents.agents.risk_mgmt.neutral_debator
   tradingagents.agents.trader.trader

Data Infrastructure
-------------------

.. autosummary::
   :toctree: generated

   tradingagents.dataflows.ccxt_adapters
   tradingagents.dataflows.crypto_cache
   tradingagents.dataflows.crypto_utils
   tradingagents.dataflows.metric_registry
   tradingagents.dataflows.onchain_loader
   tradingagents.dataflows.interface
   tradingagents.dataflows.config

Market Data Adapters
--------------------

.. autosummary::
   :toctree: generated

   tradingagents.dataflows.yfin_utils
   tradingagents.dataflows.finnhub_utils
   tradingagents.dataflows.googlenews_utils
   tradingagents.dataflows.reddit_utils
   tradingagents.dataflows.stockstats_utils

Graph & Signal Processing
-------------------------

.. autosummary::
   :toctree: generated

   tradingagents.graph.trading_graph
   tradingagents.graph.signal_processing
   tradingagents.graph.conditional_logic
   tradingagents.graph.propagation
   tradingagents.graph.reflection

Utilities
---------

.. autosummary::
   :toctree: generated

   tradingagents.agents.utils.agent_states
   tradingagents.agents.utils.agent_utils
   tradingagents.agents.utils.memory
   tradingagents.dataflows.utils 