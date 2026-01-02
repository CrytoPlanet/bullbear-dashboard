"""ETF net flow data source."""

from __future__ import annotations

from bullbear_backend.data.providers import get_provider
from bullbear_backend.data.sources.base import BaseSource
from bullbear_backend.data.types import DataResult, DataType


class EtfNetFlowSource(BaseSource):
    """Source for fetching ETF net flow from Farside Investors."""

    def __init__(self) -> None:
        self._provider = get_provider("farside")

    def fetch(self) -> DataResult:
        """Fetch current ETF net flow in USD."""
        value = self._provider.get_etf_net_flow()
        
        if value is None:
            raise ValueError("Failed to fetch ETF net flow data")
        
        return DataResult(
            data_type=DataType.ETF_NET_FLOW,
            value=value,
            provider=self._provider.name,
            metadata={"currency": "USD", "description": "现货 ETF 的净资金流入（正数）或流出（负数）"},
        )

