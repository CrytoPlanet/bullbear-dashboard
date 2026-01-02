"""Data providers module."""

from __future__ import annotations

import os

from bullbear_backend.data.providers.base import BaseProvider
from bullbear_backend.data.providers.binance import BinanceProvider
from bullbear_backend.data.providers.coinmarketcap import CoinMarketCapProvider
from bullbear_backend.data.providers.mock import MockProvider
from bullbear_backend.data.providers.taapi import TaapiProvider

__all__ = ["BinanceProvider", "CoinMarketCapProvider", "MockProvider", "TaapiProvider", "get_provider"]


def get_provider(provider_type: str) -> BaseProvider:
    """Get a provider instance based on type and environment configuration.
    
    Args:
        provider_type: One of 'binance', 'coinmarketcap', 'taapi', or 'mock'
    
    Returns:
        Provider instance
    """
    use_mock = os.getenv("USE_MOCK_DATA", "false").lower() == "true"
    
    if use_mock or provider_type == "mock":
        return MockProvider()
    
    if provider_type == "binance":
        return BinanceProvider()
    elif provider_type == "coinmarketcap":
        return CoinMarketCapProvider()
    elif provider_type == "taapi":
        return TaapiProvider()
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")
