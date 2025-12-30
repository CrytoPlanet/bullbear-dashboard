"""CoinMarketCap API provider for market data."""

from __future__ import annotations

import os

import requests

from bullbear_backend.data.providers.base import BaseProvider


class CoinMarketCapProvider(BaseProvider):
    """Provider for CoinMarketCap API.

    Provides:
    - BTC price (real-time)
    - Total crypto market cap
    - Stablecoin total market cap

    Requires CMC_API_KEY environment variable.
    """

    BASE_URL = "https://pro-api.coinmarketcap.com"

    def __init__(self) -> None:
        self._api_key = os.getenv("CMC_API_KEY")
        if not self._api_key:
            raise ValueError("CMC_API_KEY environment variable is required")

    @property
    def name(self) -> str:
        return "coinmarketcap"

    def _headers(self) -> dict[str, str]:
        return {
            "X-CMC_PRO_API_KEY": self._api_key,
            "Accept": "application/json",
        }

    def get_btc_price(self) -> float:
        """Fetch current BTC price in USD.

        Uses the /v1/cryptocurrency/quotes/latest endpoint.
        """
        url = f"{self.BASE_URL}/v1/cryptocurrency/quotes/latest"
        params = {"symbol": "BTC", "convert": "USD"}

        response = requests.get(url, headers=self._headers(), params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        return float(data["data"]["BTC"]["quote"]["USD"]["price"])

    def get_total_market_cap(self) -> float:
        """Fetch total crypto market cap in USD.

        Uses the /v1/global-metrics/quotes/latest endpoint.
        """
        url = f"{self.BASE_URL}/v1/global-metrics/quotes/latest"

        response = requests.get(url, headers=self._headers(), timeout=10)
        response.raise_for_status()

        data = response.json()
        return float(data["data"]["quote"]["USD"]["total_market_cap"])

    def get_stablecoin_market_cap(self) -> float:
        """Fetch total stablecoin market cap in USD.

        Uses the /v1/global-metrics/quotes/latest endpoint.
        """
        url = f"{self.BASE_URL}/v1/global-metrics/quotes/latest"

        response = requests.get(url, headers=self._headers(), timeout=10)
        response.raise_for_status()

        data = response.json()
        return float(data["data"]["quote"]["USD"]["stablecoin_market_cap"])

