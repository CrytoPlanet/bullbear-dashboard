"""Base class for third-party data providers."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """Abstract base class for all data providers.

    Each provider implementation handles authentication, HTTP calls,
    rate limiting, and response parsing for a specific third-party API.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name (e.g., 'coinmarketcap', 'taapi')."""
        ...

