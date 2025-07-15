"""Test crypto configuration toggle and schema validation."""

import pytest
from tradingagents.default_config import DEFAULT_CONFIG


class TestCryptoConfig:
    """Test crypto configuration settings."""

    def test_crypto_toggle_exists(self):
        """Test that crypto toggle exists in config."""
        assert "use_crypto" in DEFAULT_CONFIG
        assert isinstance(DEFAULT_CONFIG["use_crypto"], bool)

    def test_crypto_toggle_default_false(self):
        """Test that crypto toggle defaults to False."""
        assert DEFAULT_CONFIG["use_crypto"] is False

    def test_crypto_config_structure(self):
        """Test that crypto config has expected structure."""
        assert "crypto" in DEFAULT_CONFIG
        crypto_config = DEFAULT_CONFIG["crypto"]
        
        # Required keys
        required_keys = [
            "backend_url",
            "default_currency", 
            "rate_limit_delay",
            "supported_symbols",
            "symbol_mapping"
        ]
        
        for key in required_keys:
            assert key in crypto_config, f"Missing required crypto config key: {key}"

    def test_crypto_backend_url(self):
        """Test crypto backend URL is correctly set."""
        crypto_config = DEFAULT_CONFIG["crypto"]
        assert crypto_config["backend_url"] == "https://api.coingecko.com/api/v3"

    def test_crypto_symbol_mapping(self):
        """Test crypto symbol mapping contains expected entries."""
        crypto_config = DEFAULT_CONFIG["crypto"]
        symbol_mapping = crypto_config["symbol_mapping"]
        
        # Test some key mappings
        assert symbol_mapping["BTC"] == "bitcoin"
        assert symbol_mapping["ETH"] == "ethereum"
        assert symbol_mapping["BTC-USD"] == "bitcoin"
        assert symbol_mapping["ETH-USD"] == "ethereum"

    def test_crypto_supported_symbols(self):
        """Test supported symbols list."""
        crypto_config = DEFAULT_CONFIG["crypto"]
        supported_symbols = crypto_config["supported_symbols"]
        
        assert isinstance(supported_symbols, list)
        assert "BTC" in supported_symbols
        assert "ETH" in supported_symbols
        assert len(supported_symbols) > 0

    def test_crypto_rate_limit_delay(self):
        """Test rate limit delay is numeric."""
        crypto_config = DEFAULT_CONFIG["crypto"]
        rate_limit = crypto_config["rate_limit_delay"]
        
        assert isinstance(rate_limit, (int, float))
        assert rate_limit >= 0

    def test_crypto_currency_setting(self):
        """Test default currency setting."""
        crypto_config = DEFAULT_CONFIG["crypto"]
        assert crypto_config["default_currency"] == "usd"

    def test_config_toggle_integration(self):
        """Test that crypto config can be toggled."""
        # Create a modified config
        test_config = DEFAULT_CONFIG.copy()
        test_config["use_crypto"] = True
        
        assert test_config["use_crypto"] is True
        assert test_config["crypto"]["backend_url"] == "https://api.coingecko.com/api/v3"


if __name__ == "__main__":
    pytest.main([__file__]) 