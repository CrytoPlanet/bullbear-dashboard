"""Data providers module."""

from __future__ import annotations

from bullbear_backend.data.providers.base import BaseProvider
from bullbear_backend.data.providers.binance import BinanceProvider
from bullbear_backend.data.providers.coingecko import CoinGeckoProvider
from bullbear_backend.data.providers.coinmarketcap import CoinMarketCapProvider
from bullbear_backend.data.providers.farside import FarsideProvider
from bullbear_backend.data.providers.taapi import TaapiProvider

__all__ = ["BinanceProvider", "CoinGeckoProvider", "CoinMarketCapProvider", "FarsideProvider", "TaapiProvider", "get_provider"]


def get_provider(provider_type: str) -> BaseProvider:
    """Get a provider instance based on type.
    
    Args:
        provider_type: One of 'binance', 'coingecko', 'coinmarketcap', 'farside', or 'taapi'
    
    Returns:
        Provider instance
    
    Raises:
        ValueError: If provider_type is not supported
    """
    if provider_type == "binance":
        return BinanceProvider()
    elif provider_type == "coingecko":
        return CoinGeckoProvider()
    elif provider_type == "coinmarketcap":
        return CoinMarketCapProvider()
    elif provider_type == "farside":
        return FarsideProvider()
    elif provider_type == "taapi":
        return TaapiProvider()
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")
