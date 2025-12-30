"""BTC price data source."""

from __future__ import annotations

from bullbear_backend.data.providers.coinmarketcap import CoinMarketCapProvider
from bullbear_backend.data.sources.base import BaseSource
from bullbear_backend.data.types import DataResult, DataType


class BtcPriceSource(BaseSource):
    """Source for fetching BTC price from CoinMarketCap."""

    def __init__(self) -> None:
        self._provider = CoinMarketCapProvider()

    def fetch(self) -> DataResult:
        """Fetch current BTC price in USD."""
        value = self._provider.get_btc_price()

        return DataResult(
            data_type=DataType.BTC_PRICE,
            value=value,
            provider=self._provider.name,
            metadata={"currency": "USD"},
        )

