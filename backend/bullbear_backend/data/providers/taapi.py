"""TAAPI.io provider for technical indicators."""

from __future__ import annotations

import os

import requests

from bullbear_backend.data.providers.base import BaseProvider


class TaapiProvider(BaseProvider):
    """Provider for TAAPI.io API.

    Provides:
    - MA50 (50-day moving average)
    - MA200 (200-day moving average)

    Requires TAAPI_SECRET environment variable.
    """

    BASE_URL = "https://api.taapi.io"

    # Default settings for BTC MA calculation
    DEFAULT_EXCHANGE = "binance"
    DEFAULT_SYMBOL = "BTC/USDT"
    DEFAULT_INTERVAL = "1d"

    def __init__(self) -> None:
        self._secret = os.getenv("TAAPI_SECRET")
        if not self._secret:
            raise ValueError("TAAPI_SECRET environment variable is required")

    @property
    def name(self) -> str:
        return "taapi"

    def _get_ma(self, period: int) -> float:
        """Fetch moving average for given period.

        Args:
            period: Number of periods (e.g., 50 for MA50, 200 for MA200)

        Returns:
            The moving average value
        """
        url = f"{self.BASE_URL}/ma"
        params = {
            "secret": self._secret,
            "exchange": self.DEFAULT_EXCHANGE,
            "symbol": self.DEFAULT_SYMBOL,
            "interval": self.DEFAULT_INTERVAL,
            "period": period,
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        return float(data["value"])

    def get_ma50(self) -> float:
        """Fetch 50-day moving average for BTC."""
        return self._get_ma(50)

    def get_ma200(self) -> float:
        """Fetch 200-day moving average for BTC."""
        return self._get_ma(200)

