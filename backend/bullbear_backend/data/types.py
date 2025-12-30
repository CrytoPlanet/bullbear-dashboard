"""Data types and result models for the data layer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class DataType(str, Enum):
    """Supported data types that can be fetched."""

    BTC_PRICE = "btc_price"
    TOTAL_MARKET_CAP = "total_market_cap"
    STABLECOIN_MARKET_CAP = "stablecoin_market_cap"
    MA50 = "ma50"
    MA200 = "ma200"


@dataclass
class DataResult:
    """Result of a data fetch operation."""

    data_type: DataType
    value: float
    provider: str
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "data_type": self.data_type.value,
            "value": self.value,
            "provider": self.provider,
            "metadata": self.metadata or {},
        }

