"""Moving average data source."""

from __future__ import annotations

from bullbear_backend.data.providers.taapi import TaapiProvider
from bullbear_backend.data.sources.base import BaseSource
from bullbear_backend.data.types import DataResult, DataType


class MaSource(BaseSource):
    """Source for fetching moving averages from TAAPI.

    Supports MA50 and MA200 for BTC.
    """

    def __init__(self, period: int) -> None:
        """Initialize MA source.

        Args:
            period: Moving average period (50 or 200)
        """
        if period not in (50, 200):
            raise ValueError(f"Unsupported MA period: {period}. Use 50 or 200.")

        self._period = period
        self._provider = TaapiProvider()

    def fetch(self) -> DataResult:
        """Fetch moving average value."""
        if self._period == 50:
            value = self._provider.get_ma50()
            data_type = DataType.MA50
        else:
            value = self._provider.get_ma200()
            data_type = DataType.MA200

        return DataResult(
            data_type=data_type,
            value=value,
            provider=self._provider.name,
            metadata={
                "period": self._period,
                "exchange": TaapiProvider.DEFAULT_EXCHANGE,
                "symbol": TaapiProvider.DEFAULT_SYMBOL,
                "interval": TaapiProvider.DEFAULT_INTERVAL,
            },
        )

