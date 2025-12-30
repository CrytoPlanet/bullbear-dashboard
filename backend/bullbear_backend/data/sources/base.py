"""Base class for data sources."""

from __future__ import annotations

from abc import ABC, abstractmethod

from bullbear_backend.data.types import DataResult


class BaseSource(ABC):
    """Abstract base class for all data sources.

    Each source is responsible for fetching a specific type of data
    and delegating to the appropriate provider.
    """

    @abstractmethod
    def fetch(self) -> DataResult:
        """Fetch data from the provider.

        Returns:
            DataResult containing the fetched value and metadata
        """
        ...

