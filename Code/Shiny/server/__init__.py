"""
Makes the server directory a Python package and exposes key functionality.
"""

from .database import get_db_connection, load_data_from_table, load_time_series_data, load_country_data, load_weapon_stocks_data
from .queries import (
    HEAVY_WEAPONS_COLUMNS,
    AID_TYPE_CONFIG,
    WEAPON_STOCKS_COLUMNS,
    TOTAL_SUPPORT_COLUMNS,
    AID_TYPES_COLUMNS,
    COUNTRY_AID_COLUMNS,
    WEAPON_STOCKS_QUERY,
    WEAPON_STOCKS_BASE_TABLE,
    WEAPON_STOCKS_DETAIL_TABLE,
    HEAVY_WEAPONS_DELIVERY_QUERY,
    COUNTRY_AID_TABLE,  # Add this
    COUNTRY_GROUPS,
    WW2_WEAPON_CATEGORIES,
    WW2_CONFLICTS,
    WW2_EQUIPMENT_BASE_QUERY,
    WW2_EQUIPMENT_CATEGORIZED_QUERY,
    COUNTRY_LOOKUP_TABLE,  # Add this
    MAP_SUPPORT_TYPES,  # Add this
    TIME_SERIES_TABLE,  # Add this
    BUDGET_SUPPORT_COLUMNS,
    FINANCIAL_AID_COLUMNS,  # Add this
    FINANCIAL_AID_TABLE,  # Add this
    FINANCIAL_AID_QUERY,
    WW2_COMPARISON_QUERY,
    US_WARS_COMPARISON_QUERY, 
    GULF_WAR_COMPARISON_QUERY,
    DOMESTIC_COMPARISON_QUERY,
    EUROPEAN_CRISIS_QUERY,
    GERMAN_COMPARISON_QUERY,
    build_group_allocations_query,
    build_map_support_query,
)

__all__ = [
    # Functions
    "get_db_connection",
    "load_data_from_table",
    "load_time_series_data",
    "load_country_data",
    "load_weapon_stocks_data",
    "build_group_allocations_query",
    "build_map_support_query",
    "load_weapon_stocks_data",
    # Column definitions
    "TOTAL_SUPPORT_COLUMNS",
    "AID_TYPES_COLUMNS",
    "COUNTRY_AID_COLUMNS",
    "HEAVY_WEAPONS_COLUMNS",
    "WEAPON_STOCKS_COLUMNS",
    "BUDGET_SUPPORT_COLUMNS",
    "TOTAL_SUPPORT_COLUMNS",
    "AID_TYPES_COLUMNS",
    "COUNTRY_AID_COLUMNS",
    "FINANCIAL_AID_COLUMNS",
    "MAP_SUPPORT_TYPES",
    # Tables definition
    "BUDGET_SUPPORT_TABLE",
    "WEAPON_STOCKS_BASE_TABLE",
    "WEAPON_STOCKS_DETAIL_TABLE",
    "TIME_SERIES_TABLE",
    "COUNTRY_AID_TABLE",
    "COUNTRY_LOOKUP_TABLE",
    "FINANCIAL_AID_TABLE",
    "WW2_WEAPON_CATEGORIES",
    "WW2_CONFLICTS",
    "WW2_EQUIPMENT_BASE_QUERY",
    "WW2_EQUIPMENT_CATEGORIZED_QUERY",
    "WW2_COMPARISON_QUERY",
    "US_WARS_COMPARISON_QUERY",
    # Queries
    "BUDGET_SUPPORT_QUERY",
    "WEAPON_STOCKS_QUERY",
    "FINANCIAL_AID_QUERY",
    "HEAVY_WEAPONS_DELIVERY_QUERY",
    "GULF_WAR_COMPARISON_QUERY",
    "DOMESTIC_COMPARISON_QUERY",
    "EUROPEAN_CRISIS_QUERY",
    # Other constants
    "COUNTRY_GROUPS",
    "AID_TYPE_CONFIG",
    "GERMAN_COMPARISON_QUERY"
]
