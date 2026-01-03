"""ETF AUM data source."""

from __future__ import annotations

from bullbear_backend.data.providers import get_provider
from bullbear_backend.data.sources.base import BaseSource
from bullbear_backend.data.types import DataResult, DataType


class EtfAumSource(BaseSource):
    """Source for fetching ETF AUM (Assets Under Management) from yfinance."""

    def __init__(self) -> None:
        self._provider = get_provider("farside")

    def fetch(self) -> DataResult:
        """Fetch current ETF AUM in USD."""
        value = self._provider.get_etf_aum()
        
        if value is None:
            raise ValueError("Failed to fetch ETF AUM data")
        
        return DataResult(
            data_type=DataType.ETF_AUM,
            value=value,
            provider="yfinance",  # AUM is fetched from yfinance, not Farside
            metadata={"currency": "USD", "description": "ETF 的总资产管理规模"},
        )

