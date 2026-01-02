"""State machine engine for market regime detection."""

from __future__ import annotations

import logging
import math

from bullbear_backend.data import DataFetcher, DataType
from bullbear_backend.data.providers import get_provider
from bullbear_backend.state_machine.types import (
    FundingBehavior,
    MarketState,
    StateResult,
    TrendDirection,
    ValidationLayer,
)

logger = logging.getLogger(__name__)


class StateMachineEngine:
    """Enhanced state machine engine for market regime detection.

    Implements the four-quadrant state machine with validation layers:
    1. Trend structure (MA50/MA200 with slope)
    2. Funding behavior (stablecoin dynamics)
    3. Risk thermometer (ATH drawdown)
    4. ETF accelerator (ETF flow analysis)
    """

    # Class-level cache for historical market cap data (shared across instances)
    _historical_stablecoin_caps: list[float] = []
    _historical_total_caps: list[float] = []
    _max_history_size = 30  # Keep last 30 days of data

    def __init__(self, data_fetcher: DataFetcher | None = None) -> None:
        """Initialize state machine engine.

        Args:
            data_fetcher: Optional DataFetcher instance. If None, creates a new one.
        """
        self._fetcher = data_fetcher or DataFetcher()
        # Get providers for historical data access
        self._provider = get_provider("binance")
        self._coingecko_provider = get_provider("coingecko")

    def evaluate(self) -> StateResult:
        """Evaluate current market state.

        Returns:
            StateResult with current market state and validation layers
        """
        # Fetch current data
        btc_price = self._fetcher.get(DataType.BTC_PRICE).value
        ma50 = self._fetcher.get(DataType.MA50).value
        ma200 = self._fetcher.get(DataType.MA200).value
        total_market_cap = self._fetcher.get(DataType.TOTAL_MARKET_CAP).value
        stablecoin_market_cap = self._fetcher.get(DataType.STABLECOIN_MARKET_CAP).value

        # Get historical data for slope calculation and trend analysis
        historical_data = self._get_historical_data()
        
        # Get historical market cap data from external API (CoinGecko)
        historical_market_data = self._get_historical_market_cap_data()
        
        # Store current market cap data for historical analysis (for backward compatibility)
        self._update_market_cap_history(stablecoin_market_cap, total_market_cap)

        # Determine trend direction with slope
        trend, ma50_slope, ma200_slope = self._determine_trend_with_slope(
            btc_price, ma50, ma200, historical_data
        )

        # Determine funding behavior (needs historical stablecoin data)
        funding, stablecoin_change, stablecoin_ratio_change = self._determine_funding(
            stablecoin_market_cap, total_market_cap, historical_data, historical_market_data
        )
        
        # Calculate slopes for stablecoin and total market cap (for frontend display)
        # Use external API historical data if available, otherwise fall back to cache
        stablecoin_slope = 0.0
        total_slope = 0.0
        
        # Try to use external API historical data first
        if historical_market_data:
            stablecoin_history = [item[1] for item in historical_market_data.get("stablecoin_market_cap", [])]
            total_history = [item[1] for item in historical_market_data.get("total_market_cap", [])]
            
            if len(stablecoin_history) >= 10:
                stablecoin_slope = self._calculate_slope(stablecoin_history, periods=min(10, len(stablecoin_history)))
                logger.info(f"Calculated stablecoin slope from external API: {stablecoin_slope:.4f}%/day (from {len(stablecoin_history)} days)")
            
            if len(total_history) >= 10:
                total_slope = self._calculate_slope(total_history, periods=min(10, len(total_history)))
                logger.info(f"Calculated total market cap slope from external API: {total_slope:.4f}%/day (from {len(total_history)} days)")
        
        # Fallback to cache if external API data is insufficient
        if stablecoin_slope == 0.0 and len(self._historical_stablecoin_caps) >= 7:
            stablecoin_slope = self._calculate_slope(
                self._historical_stablecoin_caps, 
                periods=min(10, len(self._historical_stablecoin_caps))
            )
            logger.info(f"Calculated stablecoin slope from cache: {stablecoin_slope:.4f}%/day (from {len(self._historical_stablecoin_caps)} days)")
        
        if total_slope == 0.0 and len(self._historical_total_caps) >= 7:
            total_slope = self._calculate_slope(
                self._historical_total_caps, 
                periods=min(10, len(self._historical_total_caps))
            )
            logger.info(f"Calculated total market cap slope from cache: {total_slope:.4f}%/day (from {len(self._historical_total_caps)} days)")
        
        if stablecoin_slope == 0.0 and total_slope == 0.0:
            logger.warning("Unable to calculate market cap slopes: insufficient historical data from both external API and cache")

        # Map to market state
        state = self._map_to_state(trend, funding)

        # Determine risk level
        risk_level = self._get_risk_level(state)

        # Calculate risk thermometer (ATH drawdown)
        ath_drawdown, risk_thermometer = self._calculate_risk_thermometer(
            btc_price, historical_data
        )

        # Calculate ETF accelerator (placeholder for now)
        etf_accelerator, etf_net_flow, etf_aum = self._calculate_etf_accelerator()

        # Create validation layer
        validation = ValidationLayer(
            risk_thermometer=risk_thermometer,
            ath_drawdown=ath_drawdown,
            etf_accelerator=etf_accelerator,
            etf_net_flow=etf_net_flow,
            etf_aum=etf_aum,
        )

        # Calculate confidence
        confidence = self._calculate_confidence(
            btc_price, ma50, ma200, ma50_slope, ma200_slope, stablecoin_ratio_change
        )

        stablecoin_ratio = (stablecoin_market_cap / total_market_cap) * 100

        return StateResult(
            state=state,
            trend=trend,
            funding=funding,
            risk_level=risk_level,
            confidence=confidence,
            validation=validation,
            metadata={
                "btc_price": btc_price,
                "ma50": ma50,
                "ma200": ma200,
                "ma50_slope": ma50_slope,
                "ma200_slope": ma200_slope,
                "total_market_cap": total_market_cap,
                "stablecoin_market_cap": stablecoin_market_cap,
                "stablecoin_ratio": stablecoin_ratio,
                "stablecoin_change": stablecoin_change,
                "stablecoin_ratio_change": stablecoin_ratio_change,
                "stablecoin_slope": stablecoin_slope,
                "total_slope": total_slope,
                "ath_drawdown": ath_drawdown,
            },
        )

    def _get_historical_data(self) -> dict[str, list[float]]:
        """Get historical data for calculations.

        Returns:
            Dictionary with historical prices, MA50, MA200 values
        """
        try:
            # Try to get historical klines (works for both BinanceProvider and other providers)
            if hasattr(self._provider, "get_klines"):
                # Fetch 220 klines to ensure we have at least 10 MA200 values for slope calculation
                # (MA200 needs 200 days for first value, then 10 more for slope = 210 minimum)
                klines = self._provider.get_klines(limit=220)
                # Extract closing prices (index 4)
                closing_prices = [float(candle[4]) for candle in klines]
                
                logger.info(f"Fetched {len(closing_prices)} historical prices from Binance")
                
                # Calculate historical MAs
                ma50_history = []
                ma200_history = []
                
                for i in range(len(closing_prices)):
                    if i >= 49:  # Need at least 50 days for MA50
                        ma50_history.append(sum(closing_prices[i-49:i+1]) / 50)
                    if i >= 199:  # Need at least 200 days for MA200
                        ma200_history.append(sum(closing_prices[i-199:i+1]) / 200)
                
                logger.info(f"Calculated {len(ma50_history)} MA50 values and {len(ma200_history)} MA200 values")
                
                return {
                    "prices": closing_prices,
                    "ma50": ma50_history,
                    "ma200": ma200_history,
                }
        except Exception as e:
            # Fallback: return empty data (will use current values only)
            logger.warning(f"Failed to get historical data: {e}")
        
        return {"prices": [], "ma50": [], "ma200": []}

    def _get_historical_market_cap_data(self) -> dict[str, list[tuple[int, float]]] | None:
        """Get historical market cap data from external API (CoinGecko).
        
        Returns:
            Dictionary with 'total_market_cap' and 'stablecoin_market_cap' lists,
            each containing (timestamp, value) tuples. Returns None if API call fails.
        """
        try:
            if hasattr(self._coingecko_provider, "get_historical_market_data"):
                historical_data = self._coingecko_provider.get_historical_market_data(days=30)
                if historical_data and historical_data.get("total_market_cap"):
                    logger.info(f"Fetched {len(historical_data['total_market_cap'])} days of historical market cap data from CoinGecko")
                    return historical_data
        except Exception as e:
            logger.warning(f"Failed to get historical market cap data from CoinGecko: {e}")
        
        return None

    def _update_market_cap_history(self, stablecoin_cap: float, total_cap: float) -> None:
        """Update historical market cap data cache.
        
        Stores current values for trend analysis. This is a simple in-memory cache
        that persists across evaluations within the same process.
        Used as fallback when external API data is unavailable.
        
        Args:
            stablecoin_cap: Current stablecoin market cap
            total_cap: Current total market cap
        """
        # Add current values to history
        self._historical_stablecoin_caps.append(stablecoin_cap)
        self._historical_total_caps.append(total_cap)
        
        # Keep only last N days
        if len(self._historical_stablecoin_caps) > self._max_history_size:
            self._historical_stablecoin_caps.pop(0)
            self._historical_total_caps.pop(0)

    def _calculate_slope(self, values: list[float], periods: int = 10) -> float:
        """Calculate slope of a series over recent periods using linear regression on log scale.
        
        Uses logarithmic coordinates and linear regression to calculate slope.
        This method is more robust and provides percentage-based slope that is
        comparable across different price levels.
        
        Formula:
        1. Convert values to log scale: log_values = [log(v) for v in values]
        2. Apply linear regression: slope = Σ((x[i] - x_mean) * (log_y[i] - log_y_mean)) / Σ((x[i] - x_mean)²)
        3. Convert to percentage: slope_percent = slope * 100
        
        The slope represents the daily percentage change rate in log space,
        which is approximately the percentage change rate in linear space.

        Args:
            values: List of values (oldest to newest)
            periods: Number of recent periods to use (default: 10 days)

        Returns:
            Slope as percentage change rate per day (positive = upward, negative = downward)
            Example: 0.1 means 0.1% increase per day
        """
        if len(values) < periods:
            return 0.0
        
        # Get recent values
        recent = values[-periods:]
        
        # Filter out zero or negative values (shouldn't happen for prices/MAs, but safety check)
        valid_values = [v for v in recent if v > 0]
        if len(valid_values) < periods:
            logger.warning(f"Insufficient valid values for slope calculation: {len(valid_values)}/{periods}")
            if len(valid_values) < 2:
                return 0.0
            # Use available valid values
            recent = valid_values
        
        # Convert to log scale
        try:
            log_values = [math.log(v) for v in recent]
        except (ValueError, OverflowError) as e:
            logger.warning(f"Error converting to log scale: {e}")
            return 0.0
        
        # Linear regression on log scale
        n = len(log_values)
        x = list(range(n))  # Time indices: [0, 1, 2, ..., n-1]
        x_mean = sum(x) / n
        log_y_mean = sum(log_values) / n
        
        # Calculate numerator and denominator for linear regression
        numerator = sum((x[i] - x_mean) * (log_values[i] - log_y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        # Slope in log space (this is the daily rate of change in log space)
        slope_log = numerator / denominator
        
        # Convert to percentage change rate per day
        # In log space, the slope represents the continuous growth rate
        # For small changes, this approximates the percentage change rate
        # We multiply by 100 to get percentage
        slope_percent = slope_log * 100
        
        return slope_percent

    def _determine_trend_with_slope(
        self,
        btc_price: float,
        ma50: float,
        ma200: float,
        historical_data: dict[str, list[float]],
    ) -> tuple[TrendDirection, float, float]:
        """Determine trend direction with slope analysis.

        Rules (based on videologic.md):
        - 多头排列（趋势多）: 价格在 MA200 上方，且 MA200 走平或向上（斜率 >= 0）
        - 空头排列（趋势空）: 价格在 MA200 下方，且 MA200 趋势向下（斜率 < 0）
        - 趋势质量判定：
          * MA50 在 MA200 上方：说明中期趋势跟得上，市场有推动力
          * 价格 < MA50 < MA200：典型的空头排列，反弹仅视为压力位修复而非反转

        Args:
            btc_price: Current BTC price
            ma50: Current MA50 value
            ma200: Current MA200 value
            historical_data: Historical MA values for slope calculation

        Returns:
            Tuple of (trend, ma50_slope, ma200_slope)
        """
        # Calculate slopes
        ma50_history = historical_data.get("ma50", [])
        ma200_history = historical_data.get("ma200", [])
        
        # Calculate slopes if we have enough historical data
        if len(ma50_history) >= 10:
            ma50_slope = self._calculate_slope(ma50_history)
            logger.info(f"Calculated MA50 slope: {ma50_slope:.4f}%/day (from {len(ma50_history)} historical values)")
        else:
            ma50_slope = 0.0
            logger.warning(f"Insufficient MA50 history for slope calculation: {len(ma50_history)}/10 values")
        
        if len(ma200_history) >= 10:
            ma200_slope = self._calculate_slope(ma200_history)
            logger.info(f"Calculated MA200 slope: {ma200_slope:.4f}%/day (from {len(ma200_history)} historical values)")
        else:
            ma200_slope = 0.0
            logger.warning(f"Insufficient MA200 history for slope calculation: {len(ma200_history)}/10 values")
        
        # Determine trend based on videologic.md rules:
        # 多头排列：价格在 MA200 上方，且 MA200 走平或向上（斜率 >= 0）
        if btc_price > ma200 and ma200_slope >= 0:
            # Additional quality check: MA50 在 MA200 上方说明中期趋势跟得上
            if ma50 > ma200:
                logger.info(f"趋势多: 价格({btc_price:.0f}) > MA200({ma200:.0f}), MA200斜率({ma200_slope:.3f}%%) >= 0, MA50({ma50:.0f}) > MA200")
            return (TrendDirection.BULLISH, ma50_slope, ma200_slope)
        # 空头排列：价格在 MA200 下方，且 MA200 趋势向下（斜率 < 0）
        elif btc_price < ma200 and ma200_slope < 0:
            # Quality check: 价格 < MA50 < MA200 是典型的空头排列
            if btc_price < ma50 < ma200:
                logger.info(f"趋势空（典型空头排列）: 价格({btc_price:.0f}) < MA50({ma50:.0f}) < MA200({ma200:.0f}), MA200斜率({ma200_slope:.3f}%%) < 0")
            return (TrendDirection.BEARISH, ma50_slope, ma200_slope)
        else:
            # Edge cases: use price position relative to MA200 as primary indicator
            # If price is above MA200 but MA200 is declining, still bullish but weaker
            if btc_price > ma200:
                logger.info(f"趋势多（降级）: 价格({btc_price:.0f}) > MA200({ma200:.0f}), 但MA200斜率({ma200_slope:.3f}%%) < 0")
                return (TrendDirection.BULLISH, ma50_slope, ma200_slope)
            # If price is below MA200 but MA200 is rising, still bearish but weaker
            else:
                logger.info(f"趋势空（降级）: 价格({btc_price:.0f}) < MA200({ma200:.0f}), 但MA200斜率({ma200_slope:.3f}%%) >= 0")
                return (TrendDirection.BEARISH, ma50_slope, ma200_slope)

    def _determine_funding(
        self,
        stablecoin_market_cap: float,
        total_market_cap: float,
        historical_data: dict[str, list[float]],
        historical_market_data: dict[str, list[tuple[int, float]]] | None = None,
    ) -> tuple[FundingBehavior, float, float]:
        """Determine funding behavior from stablecoin dynamics.
        
        Based on videologic.md, uses four combination patterns:
        1. Stable ↑ + Total ↑ → 增量进攻（偏进攻/偏牛）
        2. Stable ↓ + Total ↑ → 强力进攻（最强进攻状态）
        3. Stable ↑ + Total ↓ → 去风险防守（典型去风险/防守）
        4. Stable ↓ + Total ↓ → 深度防守/撤退（更强的防守/彻底熊）

        Args:
            stablecoin_market_cap: Current stablecoin market cap
            total_market_cap: Current total market cap
            historical_data: Historical data (for trend analysis)
            historical_market_data: Historical market cap data from external API (optional)

        Returns:
            Tuple of (funding_behavior, stablecoin_change_percentage, stablecoin_ratio_change)
        """
        stablecoin_ratio = (stablecoin_market_cap / total_market_cap) * 100
        
        # Determine trends using historical data
        # Need at least 7 days of history for reliable trend detection
        min_history_days = 7
        
        # Try to use external API historical data first
        stablecoin_slope = 0.0
        total_slope = 0.0
        
        if historical_market_data:
            stablecoin_history = [item[1] for item in historical_market_data.get("stablecoin_market_cap", [])]
            total_history = [item[1] for item in historical_market_data.get("total_market_cap", [])]
            
            if len(stablecoin_history) >= 7:
                stablecoin_slope = self._calculate_slope(stablecoin_history, periods=min(10, len(stablecoin_history)))
                logger.info(f"Using external API data for funding: stablecoin_slope={stablecoin_slope:.4f}%/day")
            
            if len(total_history) >= 7:
                total_slope = self._calculate_slope(total_history, periods=min(10, len(total_history)))
                logger.info(f"Using external API data for funding: total_slope={total_slope:.4f}%/day")
        
        # Fallback to cache if external API data is insufficient
        if stablecoin_slope == 0.0 and total_slope == 0.0 and len(self._historical_stablecoin_caps) >= min_history_days:
            # Calculate slopes for stablecoin and total market cap
            stablecoin_slope = self._calculate_slope(self._historical_stablecoin_caps, periods=min(10, len(self._historical_stablecoin_caps)))
            total_slope = self._calculate_slope(self._historical_total_caps, periods=min(10, len(self._historical_total_caps)))
            logger.info(f"Using cache data for funding: stablecoin_slope={stablecoin_slope:.4f}%/day, total_slope={total_slope:.4f}%/day")
        
        if stablecoin_slope != 0.0 or total_slope != 0.0:
            
            # Determine direction: positive slope = ↑, negative slope = ↓
            stablecoin_trend = "↑" if stablecoin_slope > 0 else "↓"
            total_trend = "↑" if total_slope > 0 else "↓"
            
            # Apply four combination patterns from videologic.md
            if stablecoin_trend == "↑" and total_trend == "↑":
                # Stable ↑ + Total ↑ → 增量进攻（偏进攻/偏牛）
                funding = FundingBehavior.OFFENSIVE
                logger.info(f"资金姿态: 增量进攻 (Stable ↑ + Total ↑)")
            elif stablecoin_trend == "↓" and total_trend == "↑":
                # Stable ↓ + Total ↑ → 强力进攻（最强进攻状态）
                funding = FundingBehavior.OFFENSIVE
                logger.info(f"资金姿态: 强力进攻 (Stable ↓ + Total ↑)")
            elif stablecoin_trend == "↑" and total_trend == "↓":
                # Stable ↑ + Total ↓ → 去风险防守（典型去风险/防守）
                funding = FundingBehavior.DEFENSIVE
                logger.info(f"资金姿态: 去风险防守 (Stable ↑ + Total ↓)")
            else:  # stablecoin_trend == "↓" and total_trend == "↓"
                # Stable ↓ + Total ↓ → 深度防守/撤退（更强的防守/彻底熊）
                funding = FundingBehavior.DEFENSIVE
                logger.info(f"资金姿态: 深度防守/撤退 (Stable ↓ + Total ↓)")
            
            # Calculate changes for metadata
            # Use external API data if available, otherwise use cache
            if historical_market_data and historical_market_data.get("stablecoin_market_cap"):
                first_stablecoin = historical_market_data["stablecoin_market_cap"][0][1]
                first_total = historical_market_data["total_market_cap"][0][1] if historical_market_data.get("total_market_cap") else total_market_cap
                first_ratio = (first_stablecoin / first_total * 100) if first_total > 0 else stablecoin_ratio
                stablecoin_change = stablecoin_market_cap - first_stablecoin
                stablecoin_ratio_change = stablecoin_ratio - first_ratio
            elif self._historical_stablecoin_caps:
                stablecoin_change = stablecoin_market_cap - self._historical_stablecoin_caps[0]
                stablecoin_ratio_change = stablecoin_ratio - ((self._historical_stablecoin_caps[0] / self._historical_total_caps[0] * 100) if (self._historical_stablecoin_caps and self._historical_total_caps and self._historical_total_caps[0] > 0) else stablecoin_ratio)
            else:
                stablecoin_change = 0.0
                stablecoin_ratio_change = 0.0
            
        else:
            # Fallback: use ratio-based approach when insufficient history
            # Historical threshold: ~8% is typical
            threshold = 8.0
            stablecoin_ratio_change = stablecoin_ratio - threshold
            stablecoin_change = stablecoin_market_cap
            
            # 资金进攻：稳定币占比 < 8%（资金流入风险资产）
            # 资金防守：稳定币占比 >= 8%（资金留在稳定币中）
            if stablecoin_ratio < threshold:
                funding = FundingBehavior.OFFENSIVE
                logger.info(f"资金姿态: 进攻 (稳定币占比 {stablecoin_ratio:.2f}% < 阈值 {threshold}%)")
            else:
                funding = FundingBehavior.DEFENSIVE
                logger.info(f"资金姿态: 防守 (稳定币占比 {stablecoin_ratio:.2f}% >= 阈值 {threshold}%)")
        
        return (funding, stablecoin_change, stablecoin_ratio_change)

    def _calculate_risk_thermometer(
        self, btc_price: float, historical_data: dict[str, list[float]]
    ) -> tuple[float, str]:
        """Calculate risk thermometer based on ATH drawdown.

        Formula: ATH回撤率 = (ATH - 当前价格) / ATH * 100%
        
        This calculates the percentage drawdown from ATH (all-time high).
        Positive value means current price is below ATH.

        Risk levels (based on videologic.md):
        - < 20%: 正常体温（36-37度，可大胆进攻）
        - 20% ~ 35%: 低/中烧（37-39度，市场难受，需要修复）
        - > 35%: 高烧威胁（熊市主导概率大增）
        - > 60%: 生命体征极差（深出清阶段，处于快死透的区间）

        Args:
            btc_price: Current BTC price
            historical_data: Historical price data

        Returns:
            Tuple of (ath_drawdown_percentage, risk_thermometer_level)
        """
        prices = historical_data.get("prices", [])
        
        if not prices:
            # Fallback: use current price as ATH (for cases without historical data)
            ath = btc_price
        else:
            ath = max(prices + [btc_price])  # Include current price
        
        if ath == 0:
            return (0.0, "正常体温")
        
        # Calculate drawdown as positive percentage: (ATH - current) / ATH * 100%
        # If current price > ATH (new ATH), drawdown is negative (no drawdown)
        drawdown = ((ath - btc_price) / ath) * 100
        
        # If current price is at or above ATH, no drawdown
        if drawdown <= 0:
            return (0.0, "正常体温")
        
        # Apply thresholds from videologic.md
        if drawdown < 20:
            return (drawdown, "正常体温")
        elif drawdown < 35:
            return (drawdown, "低/中烧")
        elif drawdown < 60:
            return (drawdown, "高烧威胁")
        else:
            return (drawdown, "生命体征极差")

    def _calculate_etf_accelerator(self) -> tuple[str, float | None, float | None]:
        """Calculate ETF accelerator status.

        Uses Farside Investors data to determine ETF flow status based on historical trends.

        Rules (from statelogic.md):
        - 顺风（加速）: ETF净流入持续 > 0 (2-4周)
        - 逆风（抑制）: ETF净流入持续 < 0 (2-4周)
        - 钝化: 流出速度减缓或接近平衡
        - 未知: 无法获取数据

        Returns:
            Tuple of (etf_status, net_flow, aum)
        """
        try:
            farside_provider = get_provider("farside")
            etf_data = farside_provider.get_etf_data()
            
            net_flow = etf_data.get("net_flow")
            aum = etf_data.get("aum")
            
            if net_flow is None:
                return ("未知", None, aum)
            
            # Get historical data to determine trend (2-4 weeks = 14-28 days, use 30 days)
            history = farside_provider.get_etf_net_flow_history(days=30)
            
            if not history or len(history) < 7:
                # If we don't have enough history, fall back to single-day logic
                # Threshold for "钝化": within ±$10M
                if abs(net_flow) < 10_000_000:
                    status = "钝化"
                elif net_flow > 0:
                    status = "顺风"
                else:
                    status = "逆风"
                logger.info(f"Using single-day ETF status: {status} (insufficient history)")
                return (status, net_flow, aum)
            
            # Analyze historical trend
            # Check if flows are consistently positive or negative over the period
            positive_days = sum(1 for day in history if day['net_flow'] > 0)
            negative_days = sum(1 for day in history if day['net_flow'] < 0)
            total_days = len(history)
            
            # Calculate average flow over the period
            avg_flow = sum(day['net_flow'] for day in history) / total_days
            
            # For "持续流入/流出", we need at least 14 days (2 weeks) of consistent direction
            # And the majority of days should be in that direction
            min_consistent_days = 14
            consistency_threshold = 0.7  # 70% of days should be in the same direction
            
            # Check for 顺风 (持续流入)
            if positive_days >= min_consistent_days and positive_days / total_days >= consistency_threshold:
                # Additional check: recent flows should be positive
                recent_flows = [day['net_flow'] for day in history[-7:]]  # Last week
                if all(flow > 0 for flow in recent_flows) or sum(recent_flows) > 0:
                    status = "顺风"
                    logger.info(f"ETF 顺风: {positive_days}/{total_days} days positive, avg flow: ${avg_flow:,.0f}")
                    return (status, net_flow, aum)
            
            # Check for 逆风 (持续流出)
            if negative_days >= min_consistent_days and negative_days / total_days >= consistency_threshold:
                # Additional check: recent flows should be negative
                recent_flows = [day['net_flow'] for day in history[-7:]]  # Last week
                if all(flow < 0 for flow in recent_flows) or sum(recent_flows) < 0:
                    status = "逆风"
                    logger.info(f"ETF 逆风: {negative_days}/{total_days} days negative, avg flow: ${avg_flow:,.0f}")
                    return (status, net_flow, aum)
            
            # Check for 钝化 (流出速度减缓或接近平衡)
            # Compare recent outflow rate with earlier outflow rate
            if len(history) >= 14:
                # First half average
                first_half = history[:len(history)//2]
                first_avg = sum(day['net_flow'] for day in first_half) / len(first_half)
                
                # Second half average
                second_half = history[len(history)//2:]
                second_avg = sum(day['net_flow'] for day in second_half) / len(second_half)
                
                # If outflow is slowing down (becoming less negative) or near zero
                if first_avg < 0 and second_avg > first_avg and abs(second_avg) < abs(first_avg) * 0.5:
                    status = "钝化"
                    logger.info(f"ETF 钝化: outflow slowing from ${first_avg:,.0f} to ${second_avg:,.0f}")
                    return (status, net_flow, aum)
            
            # If near zero or mixed signals, consider it 钝化
            if abs(avg_flow) < 10_000_000:  # Less than $10M average
                status = "钝化"
                logger.info(f"ETF 钝化: average flow near zero (${avg_flow:,.0f})")
            else:
                # Mixed signals - use current day's flow as tiebreaker
                if net_flow > 0:
                    status = "顺风"
                else:
                    status = "逆风"
                logger.info(f"ETF mixed signals, using current day: {status}")
            
            return (status, net_flow, aum)
            
        except Exception as e:
            # Log error but don't fail the entire state evaluation
            logger.warning(f"Failed to fetch ETF data: {e}")
            # Return "未知" status instead of failing
            return ("未知", None, None)

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
        self,
        btc_price: float,
        ma50: float,
        ma200: float,
        ma50_slope: float,
        ma200_slope: float,
        stablecoin_ratio_change: float,
    ) -> float:
        """Calculate confidence score (0.0 to 1.0).

        Based on:
        - Trend clarity (MA arrangement and slopes)
        - Funding signal strength
        """
        # Trend confidence: based on MA arrangement and slopes
        ma_arrangement_clear = abs(ma50 - ma200) / ma200 if ma200 > 0 else 0
        # Slope is now in percentage, so we can use it directly
        # Normalize slope strength (typical good slope is 0.1-0.5% per day)
        slope_strength = (abs(ma50_slope) + abs(ma200_slope)) / 2
        # Convert percentage slope to confidence (0.1% = 0.1, scale to 0-1)
        slope_confidence = min(1.0, slope_strength / 0.5)  # 0.5% per day = max confidence
        
        trend_confidence = min(1.0, (ma_arrangement_clear * 5 + slope_confidence * 0.5))
        
        # Funding confidence: based on distance from threshold
        funding_strength = abs(stablecoin_ratio_change) / 8.0  # Normalized to threshold
        funding_confidence = min(1.0, funding_strength)
        
        # Average confidence
        return min(1.0, (trend_confidence + funding_confidence) / 2.0)
