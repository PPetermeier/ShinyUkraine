"""
Makes the server directory a Python package and exposes key functionality.
"""

from .database import (
    load_country_data,
    load_data_from_table,
    load_time_series_data,
)
from .queries import (
    HEAVY_WEAPONS_COLUMNS,
    HEAVY_WEAPONS_DELIVERY_QUERY,
    AID_TYPE_CONFIG,
    AID_TYPES_COLUMNS,
    COUNTRY_AID_COLUMNS,
    COUNTRY_AID_TABLE,  # Add this
    COUNTRY_GROUPS,
    COUNTRY_LOOKUP_TABLE,  # Add this
    MAP_SUPPORT_TYPES,  # Add this
    TIME_SERIES_TABLE,  # Add this
    TOTAL_SUPPORT_COLUMNS,BUDGET_SUPPORT_COLUMNS,
    FINANCIAL_AID_COLUMNS,  # Add this
    FINANCIAL_AID_TABLE,    # Add this
    FINANCIAL_AID_QUERY,    # Add this
    build_group_allocations_query,
    build_map_support_query,
)

__all__ = [
    # Functions
    "load_time_series_data",
    "load_country_data",
    "load_data_from_table",
    "build_group_allocations_query",
    "build_map_support_query",
    # Column definitions
    "HEAVY_WEAPONS_COLUMNS",
    "BUDGET_SUPPORT_COLUMNS",
    "TOTAL_SUPPORT_COLUMNS",
    "AID_TYPES_COLUMNS",
    "COUNTRY_AID_COLUMNS",
    "FINANCIAL_AID_COLUMNS",  
    "MAP_SUPPORT_TYPES",
    # Tables definition
    "BUDGET_SUPPORT_TABLE",
    "TIME_SERIES_TABLE",
    "COUNTRY_AID_TABLE",
    "COUNTRY_LOOKUP_TABLE",    
    "FINANCIAL_AID_TABLE", 
    # Queries 
    "BUDGET_SUPPORT_QUERY",
    "FINANCIAL_AID_QUERY", 
    "HEAVY_WEAPONS_DELIVERY_QUERY",  
    # Other constants
    "COUNTRY_GROUPS",
    "AID_TYPE_CONFIG",
]
