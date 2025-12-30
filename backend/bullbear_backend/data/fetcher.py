"""Layer 1: User-facing DataFetcher class."""

from __future__ import annotations

from bullbear_backend.data.sources.btc_price import BtcPriceSource
from bullbear_backend.data.sources.ma import MaSource
from bullbear_backend.data.sources.stablecoin_market_cap import StablecoinMarketCapSource
from bullbear_backend.data.sources.total_market_cap import TotalMarketCapSource
from bullbear_backend.data.types import DataResult, DataType


class DataFetcher:
    """User-facing data fetcher.

    This is the main entry point for fetching market data.
    Routes requests to the appropriate source based on data type.

    Example usage:
        fetcher = DataFetcher()
        btc_price = fetcher.get(DataType.BTC_PRICE)
        ma50 = fetcher.get(DataType.MA50)
    """

    def get(self, data_type: DataType) -> DataResult:
        """Fetch data by type.

        Args:
            data_type: The type of data to fetch

        Returns:
            DataResult containing the fetched value and metadata

        Raises:
            ValueError: If data_type is not supported
        """
        source = self._get_source(data_type)
        return source.fetch()

    def _get_source(self, data_type: DataType):
        """Get the appropriate source for a data type."""
        match data_type:
            case DataType.BTC_PRICE:
                return BtcPriceSource()
            case DataType.TOTAL_MARKET_CAP:
                return TotalMarketCapSource()
            case DataType.STABLECOIN_MARKET_CAP:
                return StablecoinMarketCapSource()
            case DataType.MA50:
                return MaSource(period=50)
            case DataType.MA200:
                return MaSource(period=200)
            case _:
                raise ValueError(f"Unsupported data type: {data_type}")

    def get_all(self) -> dict[DataType, DataResult]:
        """Fetch all supported data types.

        Returns:
            Dictionary mapping data type to result
        """
        results = {}
        for data_type in DataType:
            results[data_type] = self.get(data_type)
        return results

