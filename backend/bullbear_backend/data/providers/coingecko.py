"""CoinGecko API provider for market data.

CoinGecko provides a free public API that doesn't require authentication.
Rate limit: 10-50 calls/minute (free tier).
"""

from __future__ import annotations

import requests

from bullbear_backend.data.providers.base import BaseProvider


class CoinGeckoProvider(BaseProvider):
    """Provider for CoinGecko public API.

    Provides:
    - BTC price (real-time)
    - Total crypto market cap
    - Stablecoin total market cap

    No API key required for public endpoints.
    Rate limit: 10-50 calls/minute (free tier).
    """

    BASE_URL = "https://api.coingecko.com/api/v3"

    @property
    def name(self) -> str:
        return "coingecko"

    def get_btc_price(self) -> float:
        """Fetch current BTC price in USD.

        Uses the /simple/price endpoint.
        """
        url = f"{self.BASE_URL}/simple/price"
        params = {
            "ids": "bitcoin",
            "vs_currencies": "usd",
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        return float(data["bitcoin"]["usd"])

    def get_total_market_cap(self) -> float:
        """Fetch total crypto market cap in USD.

        Uses the /global endpoint.
        """
        url = f"{self.BASE_URL}/global"

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        return float(data["data"]["total_market_cap"]["usd"])

    def get_stablecoin_market_cap(self) -> float:
        """Fetch total stablecoin market cap in USD.

        Uses a single API call to get major stablecoins market cap.
        Falls back to estimation if API rate limit is hit.
        """
        # Get market cap for major stablecoins in one call
        stablecoin_ids = ["tether", "usd-coin", "binance-usd", "dai", "true-usd", "usdd", "frax"]
        url = f"{self.BASE_URL}/simple/price"
        params = {
            "ids": ",".join(stablecoin_ids),
            "vs_currencies": "usd",
            "include_market_cap": "true",
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            stablecoin_market_cap = 0.0
            
            # Sum market caps of all stablecoins
            for coin_id in stablecoin_ids:
                if coin_id in data and "usd_market_cap" in data[coin_id]:
                    stablecoin_market_cap += float(data[coin_id]["usd_market_cap"])
            
            # If we got some data, return it
            if stablecoin_market_cap > 0:
                return stablecoin_market_cap
        except Exception:
            # If API call fails (rate limit, etc.), fall through to estimation
            pass
        
        # Fallback: estimate stablecoin market cap as ~8% of total market cap
        # This is a typical ratio in crypto markets
        try:
            global_url = f"{self.BASE_URL}/global"
            global_response = requests.get(global_url, timeout=10)
            global_response.raise_for_status()
            global_data = global_response.json()
            total_market_cap = float(global_data["data"]["total_market_cap"]["usd"])
            return total_market_cap * 0.08
        except Exception:
            # Final fallback: return a reasonable estimate based on typical market conditions
            return 150_000_000_000  # ~$150B (typical stablecoin market cap)

    def get_historical_market_data(self, days: int = 30) -> dict[str, list[tuple[int, float]]]:
        """Fetch historical market cap data for trend analysis.
        
        Uses Bitcoin's market chart as a proxy for total market cap trends,
        since BTC market cap is highly correlated with total crypto market cap.
        For stablecoin market cap, we use a fixed ratio estimation.
        
        Note: CoinGecko's market_chart endpoint returns:
        - prices: [[timestamp_ms, price], ...]
        - market_caps: [[timestamp_ms, market_cap], ...]
        - total_volumes: [[timestamp_ms, volume], ...]
        
        Args:
            days: Number of days of history to fetch (default: 30)
            
        Returns:
            Dictionary with:
            - 'total_market_cap': List of (timestamp, value) tuples (estimated from BTC market cap)
            - 'stablecoin_market_cap': List of (timestamp, value) tuples (estimated as 8% of total)
        """
        try:
            # Get Bitcoin market chart (includes market cap data)
            url = f"{self.BASE_URL}/coins/bitcoin/market_chart"
            params = {
                "vs_currency": "usd",
                "days": days,
                "interval": "daily" if days <= 90 else "daily",
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # Extract market cap data
            # Format: [[timestamp_ms, market_cap], ...]
            market_caps = data.get("market_caps", [])
            
            if not market_caps:
                return {
                    "total_market_cap": [],
                    "stablecoin_market_cap": [],
                }
            
            # BTC market cap is typically 40-50% of total crypto market cap
            # We'll use 45% as an average ratio to estimate total market cap
            btc_to_total_ratio = 0.45
            
            # Convert to list of (timestamp, value) tuples
            # Estimate total market cap from BTC market cap
            total_market_cap_history = [
                (int(item[0]), float(item[1]) / btc_to_total_ratio) 
                for item in market_caps
            ]
            
            # For stablecoin market cap, estimate as ~8% of total market cap
            # This is a typical ratio, though it can vary
            stablecoin_ratio = 0.08
            stablecoin_market_cap_history = [
                (ts, total_cap * stablecoin_ratio) 
                for ts, total_cap in total_market_cap_history
            ]
            
            return {
                "total_market_cap": total_market_cap_history,
                "stablecoin_market_cap": stablecoin_market_cap_history,
            }
        except Exception as e:
            # If API call fails, return empty data
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to fetch historical market data from CoinGecko: {e}")
            return {
                "total_market_cap": [],
                "stablecoin_market_cap": [],
            }

