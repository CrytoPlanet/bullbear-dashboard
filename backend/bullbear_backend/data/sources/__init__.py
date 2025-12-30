"""Layer 2: Dedicated data sources for each data type."""

from bullbear_backend.data.sources.btc_price import BtcPriceSource
from bullbear_backend.data.sources.ma import MaSource
from bullbear_backend.data.sources.stablecoin_market_cap import StablecoinMarketCapSource
from bullbear_backend.data.sources.total_market_cap import TotalMarketCapSource

__all__ = [
    "BtcPriceSource",
    "TotalMarketCapSource",
    "StablecoinMarketCapSource",
    "MaSource",
]

