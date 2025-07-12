"""Lazy loading implementation for dashboard data and visualizations.

This module provides mechanisms for loading data on-demand rather than at startup,
improving application performance and reducing memory usage.
"""

import functools
import threading
import time
from collections.abc import Callable
from typing import Any, TypeVar

import pandas as pd
from shiny import reactive

from .database import load_data_from_table
from .queries import *

T = TypeVar("T")


class DataCache:
    """Thread-safe cache for storing loaded data with TTL support."""

    def __init__(self, default_ttl: int = 300):
        """Initialize data cache.

        Args:
            default_ttl: Default time-to-live for cache entries in seconds
        """
        self._cache: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()
        self.default_ttl = default_ttl

    def get(self, key: str) -> Any | None:
        """Get cached data if it exists and hasn't expired.

        Args:
            key: Cache key

        Returns:
            Cached data or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            if time.time() > entry["expires_at"]:
                del self._cache[key]
                return None

            entry["last_accessed"] = time.time()
            return entry["data"]

    def set(self, key: str, data: Any, ttl: int | None = None) -> None:
        """Store data in cache with TTL.

        Args:
            key: Cache key
            data: Data to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        ttl = ttl or self.default_ttl
        with self._lock:
            self._cache[key] = {
                "data": data,
                "created_at": time.time(),
                "last_accessed": time.time(),
                "expires_at": time.time() + ttl,
            }

    def invalidate(self, key: str) -> None:
        """Remove entry from cache.

        Args:
            key: Cache key to remove
        """
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary containing cache statistics
        """
        with self._lock:
            now = time.time()
            return {
                "total_entries": len(self._cache),
                "expired_entries": sum(
                    1 for entry in self._cache.values() if now > entry["expires_at"]
                ),
                "memory_usage_approx": sum(
                    len(str(entry["data"])) for entry in self._cache.values()
                ),
            }


# Global cache instance
data_cache = DataCache(default_ttl=600)  # 10-minute default TTL


def lazy_data_loader(
    cache_key: str,
    ttl: int | None = None,
    loading_placeholder: pd.DataFrame | None = None,
) -> Callable[[Callable[[], T]], Callable[[], T]]:
    """Decorator for lazy loading data with caching.

    Args:
        cache_key: Unique key for caching this data
        ttl: Time-to-live for cache entry
        loading_placeholder: Placeholder data while loading

    Returns:
        Decorated function that loads data lazily
    """

    def decorator(func: Callable[[], T]) -> Callable[[], T]:
        @functools.wraps(func)
        def wrapper() -> T:
            # Check cache first
            cached_data = data_cache.get(cache_key)
            if cached_data is not None:
                return cached_data

            # Load data and cache it
            try:
                data = func()
                data_cache.set(cache_key, data, ttl)
                return data
            except Exception as e:
                if loading_placeholder is not None:
                    return loading_placeholder
                raise e

        return wrapper

    return decorator


class LazyDataLoader:
    """Centralized lazy data loader for dashboard components."""

    def __init__(self):
        """Initialize lazy data loader."""
        self._loading_states: dict[str, bool] = {}
        self._error_states: dict[str, str | None] = {}

    @lazy_data_loader("timeseries_data", ttl=300)
    def load_timeseries_data(self) -> pd.DataFrame:
        """Load time series allocation data lazily."""
        return load_data_from_table(ALLOCATED_OVER_TIME_QUERY)

    @lazy_data_loader("country_summary_eur", ttl=600)
    def load_country_summary_eur(self) -> pd.DataFrame:
        """Load country summary data in EUR lazily."""
        return load_data_from_table(COUNTRY_SUMMARY_EUR_QUERY)

    @lazy_data_loader("country_summary_usd", ttl=600)
    def load_country_summary_usd(self) -> pd.DataFrame:
        """Load country summary data in USD lazily."""
        return load_data_from_table(COUNTRY_SUMMARY_USD_QUERY)

    @lazy_data_loader("allocations_vs_commitments", ttl=300)
    def load_allocations_vs_commitments(self) -> pd.DataFrame:
        """Load allocations vs commitments data lazily."""
        return load_data_from_table(ALLOCATIONS_VS_COMMITMENTS_QUERY)

    @lazy_data_loader("allocations_refugees_eur", ttl=300)
    def load_allocations_refugees_eur(self) -> pd.DataFrame:
        """Load allocations with refugee costs data lazily."""
        return load_data_from_table(ALLOCATIONS_REFUGEES_EUR_QUERY)

    @lazy_data_loader("bilateral_allocations_gdp", ttl=600)
    def load_bilateral_allocations_gdp(self) -> pd.DataFrame:
        """Load GDP-relative allocations data lazily."""
        return load_data_from_table(BILATERAL_ALLOCATIONS_GDP_QUERY)

    @lazy_data_loader("heavy_weapon_ranking", ttl=600)
    def load_heavy_weapon_ranking(self) -> pd.DataFrame:
        """Load heavy weapons ranking data lazily."""
        return load_data_from_table(HEAVY_WEAPON_RANKING_QUERY)

    @lazy_data_loader("financial_aid_by_type", ttl=300)
    def load_financial_aid_by_type(self) -> pd.DataFrame:
        """Load financial aid breakdown data lazily."""
        return load_data_from_table(FINANCIAL_AID_BY_TYPE_QUERY)

    @lazy_data_loader("weapon_stocks_base", ttl=600)
    def load_weapon_stocks_base(self) -> pd.DataFrame:
        """Load weapon stocks base data lazily."""
        return load_data_from_table(WEAPON_STOCKS_BASE_QUERY)

    @lazy_data_loader("historical_comparisons", ttl=3600)
    def load_historical_comparisons(self) -> dict[str, pd.DataFrame]:
        """Load all historical comparison datasets lazily."""
        return {
            "ww2_equipment": load_data_from_table(WW2_EQUIPMENT_COMPARISON_QUERY),
            "ww2_gdp": load_data_from_table(WW2_GDP_COMPARISON_QUERY),
            "us_wars": load_data_from_table(US_WARS_COMPARISON_QUERY),
            "gulf_war": load_data_from_table(GULF_WAR_COMPARISON_QUERY),
            "european_crises": load_data_from_table(EUROPEAN_CRISES_COMPARISON_QUERY),
        }

    def is_loading(self, data_key: str) -> bool:
        """Check if data is currently being loaded.

        Args:
            data_key: Data identifier

        Returns:
            True if data is being loaded
        """
        return self._loading_states.get(data_key, False)

    def get_error(self, data_key: str) -> str | None:
        """Get error message for failed data loading.

        Args:
            data_key: Data identifier

        Returns:
            Error message or None if no error
        """
        return self._error_states.get(data_key)

    def invalidate_cache(self, cache_key: str | None = None) -> None:
        """Invalidate cached data.

        Args:
            cache_key: Specific cache key to invalidate, or None for all
        """
        if cache_key:
            data_cache.invalidate(cache_key)
        else:
            data_cache.clear()


# Global lazy loader instance
lazy_loader = LazyDataLoader()


class ReactiveDataProvider:
    """Provides reactive data sources with lazy loading for Shiny."""

    def __init__(self, loader: LazyDataLoader):
        """Initialize reactive data provider.

        Args:
            loader: Lazy data loader instance
        """
        self.loader = loader

    def get_timeseries_data(self) -> reactive.Calc:
        """Get reactive time series data.

        Returns:
            Reactive calculation for time series data
        """

        @reactive.Calc
        def _timeseries_data():
            return self.loader.load_timeseries_data()

        return _timeseries_data

    def get_country_summary_data(self, currency: str = "EUR") -> reactive.Calc:
        """Get reactive country summary data.

        Args:
            currency: Currency for data (EUR or USD)

        Returns:
            Reactive calculation for country summary data
        """

        @reactive.Calc
        def _country_summary_data():
            if currency.upper() == "USD":
                return self.loader.load_country_summary_usd()
            return self.loader.load_country_summary_eur()

        return _country_summary_data

    def get_weapons_data(self) -> reactive.Calc:
        """Get reactive weapons data.

        Returns:
            Reactive calculation for weapons data
        """

        @reactive.Calc
        def _weapons_data():
            return {
                "ranking": self.loader.load_heavy_weapon_ranking(),
                "stocks": self.loader.load_weapon_stocks_base(),
            }

        return _weapons_data

    def get_financial_data(self) -> reactive.Calc:
        """Get reactive financial aid data.

        Returns:
            Reactive calculation for financial aid data
        """

        @reactive.Calc
        def _financial_data():
            return self.loader.load_financial_aid_by_type()

        return _financial_data

    def get_comparisons_data(self) -> reactive.Calc:
        """Get reactive historical comparisons data.

        Returns:
            Reactive calculation for historical comparisons data
        """

        @reactive.Calc
        def _comparisons_data():
            return self.loader.load_historical_comparisons()

        return _comparisons_data


# Global reactive data provider
reactive_data = ReactiveDataProvider(lazy_loader)
