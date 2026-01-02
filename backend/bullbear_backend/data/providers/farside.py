"""Farside Investors ETF data provider.

Farside Investors provides Bitcoin spot ETF data including:
- Daily net flows (inflows/outflows)
- Total AUM (Assets Under Management) - if available
- Historical data

This provider uses cloudscraper to bypass Cloudflare protection and 
pandas.read_html() to scrape the data from the website.

Data source: https://farside.co.uk/bitcoin-etf-flow-all-data/
Reference: https://github.com/canadiancode/btc-etf-flows
"""

from __future__ import annotations

import logging
from io import StringIO
from typing import Any

import cloudscraper
import pandas as pd
import yfinance as yf

from bullbear_backend.data.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class FarsideProvider(BaseProvider):
    """Provider for Farside Investors ETF data.
    
    Uses web scraping with cloudscraper and pandas.read_html() to extract ETF data from:
    https://farside.co.uk/bitcoin-etf-flow-all-data/
    
    Data source reference: https://github.com/canadiancode/btc-etf-flows
    
    Provides:
    - ETF net flow (daily net inflows/outflows) in USD
    - ETF AUM (total assets under management) - if available
    
    The page contains a table with columns:
    ['Date', 'IBIT', 'FBTC', 'BITB', 'ARKB', 'BTCO', 'EZBC', 'BRRR', 'HODL', 'BTCW', 'GBTC', 'BTC', 'Total']
    Where 'Total' column contains daily net flow in millions of USD.
    """

    # Farside Investors URL for Bitcoin ETF flow data
    # Data source: https://farside.co.uk/bitcoin-etf-flow-all-data/
    BASE_URL = "https://farside.co.uk/bitcoin-etf-flow-all-data/"
    
    @property
    def name(self) -> str:
        return "farside"
    
    def _read_tables(self) -> list[pd.DataFrame]:
        """Read HTML tables from Farside Investors page.
        
        Uses cloudscraper to bypass Cloudflare protection.
        
        Returns:
            List of DataFrames containing tables from the page
            
        Raises:
            Exception: If the page cannot be fetched or parsed
        """
        try:
            # Use cloudscraper to bypass Cloudflare protection
            # cloudscraper automatically handles Cloudflare challenges
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                }
            )
            
            logger.debug(f"Fetching ETF data from {self.BASE_URL} using cloudscraper...")
            response = scraper.get(self.BASE_URL, timeout=30)
            response.raise_for_status()
            
            # Use StringIO to wrap HTML string to avoid FutureWarning
            html_string = StringIO(response.text)
            tables = pd.read_html(html_string, flavor='html5lib')
            
            if tables:
                logger.info(f"Successfully parsed {len(tables)} table(s) from {self.BASE_URL}")
                return tables
            else:
                logger.warning("No tables found on the page")
                return []
            
        except Exception as e:
            error_msg = f"Failed to fetch from {self.BASE_URL}: {e}"
            logger.error(error_msg)
            # Return empty list instead of raising, so the system can continue
            return []
    
    def _parse_value(self, value: Any) -> float | None:
        """Parse a value that might be a number with formatting.
        
        Handles strings with $, commas, and negative signs.
        """
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        
        try:
            if isinstance(value, (int, float)):
                return float(value)
            
            if isinstance(value, str):
                # Remove common formatting
                cleaned = value.replace("$", "").replace(",", "").replace(" ", "").strip()
                # Handle negative values
                is_negative = cleaned.startswith("-") or cleaned.startswith("(")
                cleaned = cleaned.replace("-", "").replace("(", "").replace(")", "")
                
                if cleaned:
                    num_value = float(cleaned)
                    return -num_value if is_negative else num_value
        except (ValueError, TypeError):
            pass
        
        return None
    
    def get_etf_net_flow(self) -> float | None:
        """Fetch current day's ETF net flow (inflows - outflows).
        
        The Farside Investors page has a table with columns:
        ['Date', 'IBIT', 'FBTC', 'BITB', 'ARKB', 'BTCO', 'EZBC', 'BRRR', 'HODL', 'BTCW', 'GBTC', 'BTC', 'Total']
        The 'Total' column contains the daily net flow in millions of USD.
        
        Returns:
            Net flow in USD (positive = inflow, negative = outflow)
            Returns None if data cannot be fetched or parsed
        """
        try:
            tables = self._read_tables()
            
            if not tables:
                logger.warning("No tables found on the page")
                return None
            
            # Find the main ETF flow table (usually the second table, index 1)
            # It should have 'Date' and 'Total' columns
            main_table = None
            for table in tables:
                if len(table) == 0:
                    continue
                
                col_names = [str(col).lower() for col in table.columns]
                # Look for table with 'Date' and 'Total' columns
                if 'date' in col_names and 'total' in col_names:
                    main_table = table
                    break
            
            if main_table is None:
                logger.warning("Could not find ETF flow table with 'Date' and 'Total' columns")
                return None
            
            # Find the 'Total' column
            total_col = None
            for col in main_table.columns:
                if str(col).lower() == 'total':
                    total_col = col
                    break
            
            if total_col is None:
                logger.warning("Could not find 'Total' column in ETF flow table")
                return None
            
            # Get the latest data row (skip first row if it's NaN, skip last rows if they're statistics)
            # Data is usually in chronological order, with latest date first or last
            date_col = None
            for col in main_table.columns:
                if str(col).lower() == 'date':
                    date_col = col
                    break
            
            # Find the latest data row by iterating from the end
            # Data is sorted chronologically: oldest first, newest last (before statistics rows)
            # Statistics rows are at the end: Total, Average, Maximum, Minimum
            # So the latest data is the last valid row before statistics rows
            
            # Iterate from the end to find the latest valid data row
            for idx in range(len(main_table) - 1, -1, -1):
                row = main_table.iloc[idx]
                
                if not date_col:
                    continue
                
                date_val = row[date_col]
                
                # Skip if date is NaN
                if pd.isna(date_val):
                    continue
                
                # Skip statistics rows (Total, Average, Maximum, Minimum)
                date_str = str(date_val).lower()
                if any(stat in date_str for stat in ['average', 'maximum', 'minimum', 'total', 'sum']):
                    continue
                
                # Get the Total value
                total_val = row[total_col]
                
                # Skip if NaN
                if pd.isna(total_val):
                    continue
                
                # Parse the value (handles parentheses for negative numbers)
                flow_value = self._parse_value(total_val)
                
                if flow_value is not None:
                    # Values in the table are in millions, convert to actual USD
                    # Check if value seems to be in millions (typically between -2000 and 2000)
                    if abs(flow_value) < 10000:  # Likely in millions
                        flow_value = flow_value * 1_000_000
                    
                    # Validate range
                    if -10_000_000_000 <= flow_value <= 10_000_000_000:
                        # Found the latest valid data row
                        logger.info(f"Found latest ETF net flow: {flow_value:,.0f} USD (Date: {date_val})")
                        return flow_value
            
            # If we get here, no valid data was found
            logger.warning("Could not find valid ETF net flow data in the table")
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch ETF net flow from Farside Investors: {e}")
            return None
    
    def _parse_aum_value(self, value: Any) -> float | None:
        """Parse AUM value that might have B (billions) or M (millions) suffix.
        
        Returns value in USD.
        """
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        
        try:
            if isinstance(value, (int, float)):
                return float(value)
            
            if isinstance(value, str):
                # Remove common formatting
                cleaned = value.replace("$", "").replace(",", "").replace(" ", "").strip().upper()
                
                # Handle B (billions) and M (millions)
                multiplier = 1.0
                if "B" in cleaned:
                    multiplier = 1_000_000_000
                    cleaned = cleaned.replace("B", "")
                elif "M" in cleaned:
                    multiplier = 1_000_000
                    cleaned = cleaned.replace("M", "")
                
                if cleaned:
                    num_value = float(cleaned) * multiplier
                    # AUM should be positive and reasonable
                    if 1_000_000_000 <= num_value <= 1_000_000_000_000:
                        return num_value
        except (ValueError, TypeError):
            pass
        
        return None
    
    def get_etf_aum(self) -> float | None:
        """Fetch total ETF AUM (Assets Under Management) using yfinance.
        
        Sums up AUM from all major Bitcoin spot ETFs:
        IBIT, FBTC, BITB, ARKB, BTCO, EZBC, BRRR, HODL, BTCW, GBTC
        
        Returns:
            Total AUM in USD
            Returns None if data cannot be fetched or parsed
        """
        # List of major Bitcoin spot ETF tickers
        etf_tickers = [
            "IBIT",  # iShares Bitcoin Trust
            "FBTC",  # Fidelity Wise Origin Bitcoin Fund
            "BITB",  # Bitwise Bitcoin ETF
            "ARKB",  # ARK 21Shares Bitcoin ETF
            "BTCO",  # Invesco Galaxy Bitcoin ETF
            "EZBC",  # Franklin Bitcoin ETF
            "BRRR",  # Valkyrie Bitcoin Fund
            "HODL",  # VANECK BITCOIN TRUST
            "BTCW",  # WisdomTree Bitcoin Fund
            "GBTC",  # Grayscale Bitcoin Trust
        ]
        
        total_aum = 0.0
        successful_fetches = 0
        
        try:
            for ticker_symbol in etf_tickers:
                try:
                    ticker = yf.Ticker(ticker_symbol)
                    info = ticker.info
                    
                    # Get totalAssets from yfinance info
                    # totalAssets is in USD
                    total_assets = info.get("totalAssets")
                    
                    if total_assets is not None and isinstance(total_assets, (int, float)):
                        total_aum += float(total_assets)
                        successful_fetches += 1
                        logger.debug(f"Fetched AUM for {ticker_symbol}: ${total_assets:,.0f}")
                    else:
                        logger.warning(f"Could not get totalAssets for {ticker_symbol}")
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch AUM for {ticker_symbol}: {e}")
                    continue
            
            if successful_fetches == 0:
                logger.warning("Could not fetch AUM for any ETF")
                return None
            
            if total_aum > 0:
                logger.info(f"Total ETF AUM: ${total_aum:,.0f} USD (from {successful_fetches}/{len(etf_tickers)} ETFs)")
                return total_aum
            else:
                logger.warning("Total AUM is zero or negative")
                return None
                
        except Exception as e:
            logger.error(f"Failed to fetch ETF AUM using yfinance: {e}")
            return None
    
    def get_etf_net_flow_history(self, days: int = 30) -> list[dict[str, Any]] | None:
        """Fetch historical ETF net flow data.
        
        Args:
            days: Number of days of history to fetch (default: 30, covers 2-4 weeks)
        
        Returns:
            List of dictionaries with 'date' and 'net_flow' keys, sorted by date (oldest first)
            Returns None if data cannot be fetched or parsed
        """
        try:
            tables = self._read_tables()
            
            if not tables:
                logger.warning("No tables found on the page")
                return None
            
            # Find the main ETF flow table
            main_table = None
            for table in tables:
                if len(table) == 0:
                    continue
                
                col_names = [str(col).lower() for col in table.columns]
                if 'date' in col_names and 'total' in col_names:
                    main_table = table
                    break
            
            if main_table is None:
                logger.warning("Could not find ETF flow table with 'Date' and 'Total' columns")
                return None
            
            # Find columns
            total_col = None
            date_col = None
            for col in main_table.columns:
                if str(col).lower() == 'total':
                    total_col = col
                elif str(col).lower() == 'date':
                    date_col = col
            
            if total_col is None or date_col is None:
                logger.warning("Could not find required columns in ETF flow table")
                return None
            
            # Collect all valid data rows
            history = []
            for idx in range(len(main_table)):
                row = main_table.iloc[idx]
                
                date_val = row[date_col]
                if pd.isna(date_val):
                    continue
                
                # Skip statistics rows
                date_str = str(date_val).lower()
                if any(stat in date_str for stat in ['average', 'maximum', 'minimum', 'total', 'sum']):
                    continue
                
                total_val = row[total_col]
                if pd.isna(total_val):
                    continue
                
                # Parse the value
                flow_value = self._parse_value(total_val)
                
                if flow_value is not None:
                    # Convert from millions to actual USD
                    if abs(flow_value) < 10000:
                        flow_value = flow_value * 1_000_000
                    
                    # Validate range
                    if -10_000_000_000 <= flow_value <= 10_000_000_000:
                        history.append({
                            'date': date_val,
                            'net_flow': flow_value
                        })
            
            if not history:
                logger.warning("Could not find valid ETF net flow history data")
                return None
            
            # Sort by date (oldest first) and return last N days
            # Note: history is already in chronological order (oldest to newest)
            # Return the most recent N days
            recent_history = history[-days:] if len(history) > days else history
            
            logger.info(f"Fetched {len(recent_history)} days of ETF net flow history")
            return recent_history
            
        except Exception as e:
            logger.error(f"Failed to fetch ETF net flow history: {e}")
            return None
    
    def get_etf_data(self) -> dict[str, Any]:
        """Fetch both ETF net flow and AUM in a single call.
        
        Returns:
            Dictionary with 'net_flow' and 'aum' keys
        """
        return {
            "net_flow": self.get_etf_net_flow(),
            "aum": self.get_etf_aum(),
        }

