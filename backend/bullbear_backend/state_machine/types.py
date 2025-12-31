"""State machine types and enums."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class TrendDirection(str, Enum):
    """Trend direction: bullish or bearish."""

    BULLISH = "趋势多"  # Bullish trend
    BEARISH = "趋势空"  # Bearish trend


class FundingBehavior(str, Enum):
    """Funding behavior: offensive or defensive."""

    OFFENSIVE = "资金进攻"  # Capital offensive
    DEFENSIVE = "资金防守"  # Capital defensive


class MarketState(str, Enum):
    """Four-quadrant market states."""

    BULL_OFFENSIVE = "牛市进攻"  # Bull market offensive
    BULL_DEFENSIVE = "牛市修复"  # Bull market defensive
    BEAR_OFFENSIVE = "熊市反弹"  # Bear market offensive
    BEAR_DEFENSIVE = "熊市消化"  # Bear market defensive


@dataclass
class StateResult:
    """Result of state machine evaluation."""

    state: MarketState
    trend: TrendDirection
    funding: FundingBehavior
    risk_level: str  # "HIGH", "MEDIUM", "LOW"
    confidence: float  # 0.0 to 1.0
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "state": self.state.value,
            "trend": self.trend.value,
            "funding": self.funding.value,
            "risk_level": self.risk_level,
            "confidence": self.confidence,
            "metadata": self.metadata or {},
        }

