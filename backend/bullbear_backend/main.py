"""FastAPI application entry point."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from bullbear_backend.data import DataFetcher, DataType

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="BullBear Backend", version="0.1.0")


@app.get("/api/health")
def health() -> dict[str, object]:
    """Health check endpoint."""
    return {"ok": True, "service": "bullbear-backend"}


@app.get("/api/data/{data_type}")
def get_data(data_type: str) -> dict[str, object]:
    """Fetch market data by type.

    Args:
        data_type: One of: btc_price, total_market_cap, stablecoin_market_cap, ma50, ma200

    Returns:
        DataResult as JSON
    """
    # Validate data type
    try:
        dtype = DataType(data_type)
    except ValueError:
        valid_types = [t.value for t in DataType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid data_type: {data_type}. Valid types: {valid_types}",
        )

    # Fetch data
    try:
        fetcher = DataFetcher()
        result = fetcher.get(dtype)
        return {"ok": True, **result.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {e}")


@app.get("/api/data")
def get_all_data() -> dict[str, object]:
    """Fetch all market data types.

    Returns:
        Dictionary with all data types and their values
    """
    try:
        fetcher = DataFetcher()
        results = fetcher.get_all()
        return {
            "ok": True,
            "data": {dtype.value: result.to_dict() for dtype, result in results.items()},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {e}")
