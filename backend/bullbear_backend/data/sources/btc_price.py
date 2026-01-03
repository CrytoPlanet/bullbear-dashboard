"""BTC price data source."""

from __future__ import annotations

from bullbear_backend.data.providers import get_provider
from bullbear_backend.data.sources.base import BaseSource
from bullbear_backend.data.types import DataResult, DataType


class BtcPriceSource(BaseSource):
    """Source for fetching BTC price from CoinGecko (free API, no key required)."""

    def __init__(self) -> None:
        self._provider = get_provider("coingecko")

    def fetch(self) -> DataResult:
        """Fetch current BTC price in USD."""
        value = self._provider.get_btc_price()

        return DataResult(
            data_type=DataType.BTC_PRICE,
            value=value,
            provider=self._provider.name,
            metadata={"currency": "USD"},
        )

