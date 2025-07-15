Quick Start
===========

This guide will get you up and running with TradingAgents in minutes.

Basic Usage
-----------

1. **Import the core modules:**

.. code-block:: python

   from tradingagents.dataflows.interface import (
       get_exchange_ohlcv_data,
       get_exchange_order_book,
       compare_crypto_exchanges
   )
   from tradingagents.dataflows.crypto_cache import CryptoCacheManager

2. **Fetch cryptocurrency data:**

.. code-block:: python

   # Get Bitcoin price data from Binance
   btc_data = get_exchange_ohlcv_data('binance', 'BTC/USDT', '1h', 100)
   print(f"Latest BTC price: ${btc_data['close'].iloc[-1]:,.2f}")

3. **Compare prices across exchanges:**

.. code-block:: python

   # Compare BTC prices across multiple exchanges
   comparison = compare_crypto_exchanges(
       'BTC/USDT', 
       'binance,kraken,coinbase'
   )
   print(comparison)

4. **Analyze order book depth:**

.. code-block:: python

   # Get order book data
   order_book = get_exchange_order_book('kraken', 'ETH/USD', 20)
   print(f"Best bid: ${order_book['best_bid']}")
   print(f"Best ask: ${order_book['best_ask']}")
   print(f"Spread: {order_book['spread_percentage']:.3f}%")

Running with Caching
--------------------

Enable Redis caching for better performance:

.. code-block:: python

   # Initialize cache manager
   cache = CryptoCacheManager()
   
   # Check Redis status
   if cache.is_redis_available():
       print("✅ Redis caching enabled")
   else:
       print("⚠️  Redis unavailable, using direct API calls")

Multi-Agent Example
-------------------

Here's a simple example using the multi-agent framework:

.. code-block:: python

   from tradingagents.agents.analysts.market_analyst import MarketAnalyst
   from tradingagents.agents.managers.risk_manager import RiskManager
   
   # Initialize agents
   analyst = MarketAnalyst()
   risk_manager = RiskManager()
   
   # Analyze market conditions
   btc_analysis = analyst.analyze_market('BTC/USDT')
   risk_assessment = risk_manager.assess_risk(btc_analysis)
   
   print(f"Market sentiment: {btc_analysis['sentiment']}")
   print(f"Risk level: {risk_assessment['risk_level']}")

On-Chain Analytics
------------------

Access blockchain metrics:

.. code-block:: python

   from tradingagents.dataflows.onchain_loader import get_onchain_metrics
   
   # Get Bitcoin network health
   metrics = get_onchain_metrics('BTC', ['active_addresses', 'hash_rate'])
   print(f"Active addresses: {metrics['active_addresses']:,}")
   print(f"Hash rate: {metrics['hash_rate']:.2e} H/s")

CLI Interface
-------------

TradingAgents includes a command-line interface:

.. code-block:: bash

   # Start the CLI
   python -m tradingagents.cli.main
   
   # Or use the main entry point
   python main.py

For more detailed examples, see the :doc:`tutorials/index` section.

Next Steps
----------

* Explore the complete :doc:`api/index`
* Run the example notebooks in :doc:`examples/index`
* Learn about advanced features in the tutorials 