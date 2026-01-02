"""Stablecoin total market cap data source."""

from __future__ import annotations

from bullbear_backend.data.providers import get_provider
from bullbear_backend.data.sources.base import BaseSource
from bullbear_backend.data.types import DataResult, DataType


class StablecoinMarketCapSource(BaseSource):
    """Source for fetching stablecoin total market cap from CoinGecko (free API, no key required)."""

    def __init__(self) -> None:
        self._provider = get_provider("coingecko")

    def fetch(self) -> DataResult:
        """Fetch total stablecoin market cap in USD."""
        value = self._provider.get_stablecoin_market_cap()

        return DataResult(
            data_type=DataType.STABLECOIN_MARKET_CAP,
            value=value,
            provider=self._provider.name,
            metadata={"currency": "USD"},
        )

