Installation
============

TradingAgents supports Python 3.10+ and can be installed via pip or conda.

Requirements
------------

* Python 3.10 or higher
* Redis server (optional, but recommended for production)
* Git (for development installation)

Quick Install
-------------

.. code-block:: bash

   pip install -e ".[docs,ops,dev]"

Development Installation
------------------------

1. Clone the repository:

.. code-block:: bash

   git clone https://github.com/TauricResearch/TradingAgents.git
   cd TradingAgents

2. Create and activate a conda environment:

.. code-block:: bash

   conda create -n ca-trading python=3.11
   conda activate ca-trading

3. Install the package with all dependencies:

.. code-block:: bash

   pip install -e ".[docs,ops,dev]"

Redis Setup (Recommended)
-------------------------

For optimal performance, install and configure Redis:

**Windows:**

.. code-block:: bash

   # Install Redis via Chocolatey
   choco install redis-64

**Linux/macOS:**

.. code-block:: bash

   # Ubuntu/Debian
   sudo apt-get install redis-server
   
   # macOS with Homebrew
   brew install redis

Environment Configuration
-------------------------

Create a ``.env`` file in your project root:

.. code-block:: bash

   # API Keys (optional)
   COINGECKO_API_KEY=your_api_key_here
   GLASSNODE_API_KEY=your_api_key_here
   
   # Redis Configuration
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0

Verification
------------

Test your installation:

.. code-block:: python

   import tradingagents
   from tradingagents.dataflows.crypto_cache import CryptoCacheManager
   
   # Test basic import
   print(f"TradingAgents version: {tradingagents.__version__}")
   
   # Test Redis connection (optional)
   cache = CryptoCacheManager()
   print(f"Redis connection: {cache.is_redis_available()}")

Next Steps
----------

* Read the :doc:`quickstart` guide
* Explore the :doc:`tutorials/index`
* Check out the :doc:`examples/index` 