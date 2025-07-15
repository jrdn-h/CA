import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_dir": "/Users/yluo/Documents/Code/ScAI/FR1-data",
    "data_cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
        "dataflows/data_cache",
    ),
    # LLM settings
    "llm_provider": "openai",
    "deep_think_llm": "o4-mini",
    "quick_think_llm": "gpt-4o-mini",
    "backend_url": os.getenv("BACKEND_URL", "https://api.openai.com/v1"),
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    # Tool settings
    "online_tools": True,
    # Crypto settings
    "use_crypto": False,
    "crypto": {
        "backend_url": "https://api.coingecko.com/api/v3",
        "default_currency": "usd",
        "rate_limit_delay": 0.1,
        "supported_symbols": ["BTC", "ETH", "ADA", "SOL", "DOT", "MATIC"],
        "symbol_mapping": {
            "BTC": "bitcoin",
            "ETH": "ethereum", 
            "BTC-USD": "bitcoin",
            "ETH-USD": "ethereum",
            "ADA": "cardano",
            "SOL": "solana",
            "DOT": "polkadot",
            "MATIC": "polygon",
        }
    },
}
