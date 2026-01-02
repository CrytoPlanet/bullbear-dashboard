"""Binance API provider for price data and moving averages."""

from __future__ import annotations

import os

import requests

from bullbear_backend.data.providers.base import BaseProvider


class BinanceProvider(BaseProvider):
    """Provider for Binance public API.

    Provides:
    - BTC price (real-time)
    - Historical klines (candlestick data)
    - MA50 / MA200 (calculated from daily closes)

    No API key required for public endpoints.
    Rate limit: 1200 requests/minute.

    Uses Binance.US by default (works in US), can be overridden with
    BINANCE_BASE_URL environment variable for global Binance.
    """

    # Default to Binance.US (works in US), can override via env var
    DEFAULT_BASE_URL = "https://api.binance.us/api/v3"
    BASE_URL = os.getenv("BINANCE_BASE_URL", DEFAULT_BASE_URL)

    # Default settings for BTC data
    DEFAULT_SYMBOL = "BTCUSDT"
    DEFAULT_INTERVAL = "1d"  # Daily candles

    @property
    def name(self) -> str:
        return "binance"

    def get_klines(self, symbol: str | None = None, interval: str | None = None, limit: int = 200) -> list[list]:
        """Fetch candlestick/kline data.

        Args:
            symbol: Trading pair (default: BTCUSDT)
            interval: Candle interval (default: 1d)
            limit: Number of candles to fetch (max 1000, default 200)

        Returns:
            List of klines, each containing:
            [open_time, open, high, low, close, volume, close_time, ...]
        """
        url = f"{self.BASE_URL}/klines"
        params = {
            "symbol": symbol or self.DEFAULT_SYMBOL,
            "interval": interval or self.DEFAULT_INTERVAL,
            "limit": limit,
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        return response.json()

    def _get_closing_prices(self, limit: int = 200) -> list[float]:
        """Fetch closing prices from klines.

        Args:
            limit: Number of daily candles to fetch

        Returns:
            List of closing prices (oldest to newest)
        """
        klines = self.get_klines(limit=limit)
        # Index 4 is the closing price
        return [float(candle[4]) for candle in klines]

    def get_ma(self, period: int) -> float:
        """Calculate moving average for given period.

        Args:
            period: Number of periods (e.g., 50 for MA50, 200 for MA200)

        Returns:
            The moving average value
        """
        # Fetch enough candles for the period
        closing_prices = self._get_closing_prices(limit=period)

        if len(closing_prices) < period:
            raise ValueError(f"Not enough data for MA{period}. Got {len(closing_prices)} candles.")

        return sum(closing_prices) / period

    def get_ma50(self) -> float:
        """Fetch 50-day moving average for BTC."""
        return self.get_ma(50)

    def get_ma200(self) -> float:
        """Fetch 200-day moving average for BTC."""
        return self.get_ma(200)

    def get_ma_both(self) -> dict[str, float]:
        """Fetch both MA50 and MA200 in a single API call.

        This is more efficient as it only makes one request to Binance.

        Returns:
            Dict with 'ma50' and 'ma200' keys
        """
        # Fetch 200 candles (enough for both MAs)
        closing_prices = self._get_closing_prices(limit=200)

        if len(closing_prices) < 200:
            raise ValueError(f"Not enough data. Got {len(closing_prices)} candles, need 200.")

        ma200 = sum(closing_prices) / 200
        ma50 = sum(closing_prices[-50:]) / 50  # Last 50 days

        return {"ma50": ma50, "ma200": ma200}

    def get_btc_price(self) -> float:
        """Fetch current BTC price in USDT.

        Uses the ticker endpoint for real-time price.
        """
        url = f"{self.BASE_URL}/ticker/price"
        params = {"symbol": self.DEFAULT_SYMBOL}

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        return float(data["price"])

