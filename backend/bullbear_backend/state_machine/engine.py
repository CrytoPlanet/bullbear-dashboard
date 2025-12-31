"""State machine engine for market regime detection."""

from __future__ import annotations

from bullbear_backend.data import DataFetcher, DataType
from bullbear_backend.state_machine.types import (
    FundingBehavior,
    MarketState,
    StateResult,
    TrendDirection,
)


class StateMachineEngine:
    """Simple state machine engine for market regime detection.

    This is the simplest implementation that:
    1. Determines trend direction from MA50/MA200
    2. Determines funding behavior from stablecoin ratio
    3. Maps to one of four market states
    """

    def __init__(self, data_fetcher: DataFetcher | None = None) -> None:
        """Initialize state machine engine.

        Args:
            data_fetcher: Optional DataFetcher instance. If None, creates a new one.
        """
        self._fetcher = data_fetcher or DataFetcher()

    def evaluate(self) -> StateResult:
        """Evaluate current market state.

        Returns:
            StateResult with current market state and metadata
        """
        # Fetch all required data
        btc_price = self._fetcher.get(DataType.BTC_PRICE).value
        ma50 = self._fetcher.get(DataType.MA50).value
        ma200 = self._fetcher.get(DataType.MA200).value
        total_market_cap = self._fetcher.get(DataType.TOTAL_MARKET_CAP).value
        stablecoin_market_cap = self._fetcher.get(DataType.STABLECOIN_MARKET_CAP).value

        # Determine trend direction
        # Simple rule: If BTC > MA50 > MA200, bullish; otherwise bearish
        trend = self._determine_trend(btc_price, ma50, ma200)

        # Determine funding behavior
        # Simple rule: If stablecoin ratio is decreasing, offensive; otherwise defensive
        # For now, we use a threshold: if stablecoin/total < 8%, offensive
        stablecoin_ratio = (stablecoin_market_cap / total_market_cap) * 100
        funding = self._determine_funding(stablecoin_ratio)

        # Map to market state
        state = self._map_to_state(trend, funding)

        # Determine risk level
        risk_level = self._get_risk_level(state)

        # Calculate confidence (simple heuristic)
        confidence = self._calculate_confidence(btc_price, ma50, ma200, stablecoin_ratio)

        return StateResult(
            state=state,
            trend=trend,
            funding=funding,
            risk_level=risk_level,
            confidence=confidence,
            metadata={
                "btc_price": btc_price,
                "ma50": ma50,
                "ma200": ma200,
                "total_market_cap": total_market_cap,
                "stablecoin_market_cap": stablecoin_market_cap,
                "stablecoin_ratio": stablecoin_ratio,
            },
        )

    def _determine_trend(self, btc_price: float, ma50: float, ma200: float) -> TrendDirection:
        """Determine trend direction from moving averages.

        Simple rule: If BTC > MA50 > MA200, bullish trend.
        Otherwise, bearish trend.
        """
        if btc_price > ma50 > ma200:
            return TrendDirection.BULLISH
        else:
            return TrendDirection.BEARISH

    def _determine_funding(self, stablecoin_ratio: float) -> FundingBehavior:
        """Determine funding behavior from stablecoin ratio.

        Simple rule: If stablecoin ratio < 8%, offensive (money flowing into risk assets).
        Otherwise, defensive (money staying in stablecoins).
        """
        # Threshold: 8% is a reasonable historical average
        # Lower ratio = more money in risk assets = offensive
        if stablecoin_ratio < 8.0:
            return FundingBehavior.OFFENSIVE
        else:
            return FundingBehavior.DEFENSIVE

    def _map_to_state(
        self, trend: TrendDirection, funding: FundingBehavior
    ) -> MarketState:
        """Map trend and funding to market state."""
        if trend == TrendDirection.BULLISH and funding == FundingBehavior.OFFENSIVE:
            return MarketState.BULL_OFFENSIVE
        elif trend == TrendDirection.BULLISH and funding == FundingBehavior.DEFENSIVE:
            return MarketState.BULL_DEFENSIVE
        elif trend == TrendDirection.BEARISH and funding == FundingBehavior.OFFENSIVE:
            return MarketState.BEAR_OFFENSIVE
        else:  # BEARISH + DEFENSIVE
            return MarketState.BEAR_DEFENSIVE

    def _get_risk_level(self, state: MarketState) -> str:
        """Get risk level for a market state."""
        risk_map = {
            MarketState.BULL_OFFENSIVE: "HIGH",
            MarketState.BULL_DEFENSIVE: "MEDIUM",
            MarketState.BEAR_OFFENSIVE: "MEDIUM",
            MarketState.BEAR_DEFENSIVE: "LOW",
        }
        return risk_map[state]

    def _calculate_confidence(
        self, btc_price: float, ma50: float, ma200: float, stablecoin_ratio: float
    ) -> float:
        """Calculate confidence score (0.0 to 1.0).

        Simple heuristic based on how clear the signals are.
        """
        # Trend confidence: based on how far price is from MAs
        price_ma50_diff = abs(btc_price - ma50) / ma50
        ma50_ma200_diff = abs(ma50 - ma200) / ma200 if ma200 > 0 else 0

        trend_confidence = min(1.0, (price_ma50_diff + ma50_ma200_diff) * 10)

        # Funding confidence: based on how far from threshold
        threshold = 8.0
        funding_diff = abs(stablecoin_ratio - threshold) / threshold
        funding_confidence = min(1.0, funding_diff * 5)

        # Average confidence
        return (trend_confidence + funding_confidence) / 2.0

