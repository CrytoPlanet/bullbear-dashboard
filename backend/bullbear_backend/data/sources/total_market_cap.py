"""Total crypto market cap data source."""

from __future__ import annotations

from bullbear_backend.data.providers.coinmarketcap import CoinMarketCapProvider
from bullbear_backend.data.sources.base import BaseSource
from bullbear_backend.data.types import DataResult, DataType


class TotalMarketCapSource(BaseSource):
    """Source for fetching total crypto market cap from CoinMarketCap."""

    def __init__(self) -> None:
        self._provider = CoinMarketCapProvider()

    def fetch(self) -> DataResult:
        """Fetch total crypto market cap in USD."""
        value = self._provider.get_total_market_cap()

        return DataResult(
            data_type=DataType.TOTAL_MARKET_CAP,
            value=value,
            provider=self._provider.name,
            metadata={"currency": "USD"},
        )

