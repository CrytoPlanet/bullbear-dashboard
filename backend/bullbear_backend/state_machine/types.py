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
class ValidationLayer:
    """Validation layer results (risk thermometer and ETF accelerator)."""

    risk_thermometer: str  # "正常体温", "低/中烧", "高烧威胁", "生命体征极差"
    ath_drawdown: float  # ATH回撤率 (percentage)
    ath_price: float | None  # ATH价格 (USD)
    etf_accelerator: str  # "顺风", "逆风", "钝化"
    etf_net_flow: float | None  # ETF净流入/流出 (if available)
    etf_aum: float | None  # ETF管理规模 (if available)
    etf_flow_14d_sum: float | None  # 近14天净流入合计
    etf_flow_pos_ratio: float | None  # 近周期净流入为正的天数占比
    etf_flow_recent_avg: float | None  # 近7天日均净流入
    etf_flow_prev_avg: float | None  # 前7天日均净流入
    etf_flow_trend: str | None  # "up" | "down" | "flat"
    etf_aum_trend: str | None  # "up" | "down" | "flat"


@dataclass
class StateResult:
    """Result of state machine evaluation."""

    state: MarketState
    trend: TrendDirection
    funding: FundingBehavior
    risk_level: str  # "HIGH", "MEDIUM", "LOW"
    confidence: float  # 0.0 to 1.0
    validation: ValidationLayer  # 校验层
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "state": self.state.value,
            "trend": self.trend.value,
            "funding": self.funding.value,
            "risk_level": self.risk_level,
            "confidence": self.confidence,
            "validation": {
                "risk_thermometer": self.validation.risk_thermometer,
                "ath_drawdown": self.validation.ath_drawdown,
                "ath_price": self.validation.ath_price,
                "etf_accelerator": self.validation.etf_accelerator,
                "etf_net_flow": self.validation.etf_net_flow,
                "etf_aum": self.validation.etf_aum,
                "etf_flow_14d_sum": self.validation.etf_flow_14d_sum,
                "etf_flow_pos_ratio": self.validation.etf_flow_pos_ratio,
                "etf_flow_recent_avg": self.validation.etf_flow_recent_avg,
                "etf_flow_prev_avg": self.validation.etf_flow_prev_avg,
                "etf_flow_trend": self.validation.etf_flow_trend,
                "etf_aum_trend": self.validation.etf_aum_trend,
            },
            "metadata": self.metadata or {},
        }

