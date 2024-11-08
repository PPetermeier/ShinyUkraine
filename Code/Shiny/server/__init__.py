"""
Makes the server directory a Python package and exposes key functionality.
"""
from .database import (
    load_time_series_data,
    load_country_data,
    load_data_from_table,
)

from .queries import (
    TOTAL_SUPPORT_COLUMNS,
    AID_TYPES_COLUMNS,
    COUNTRY_AID_COLUMNS,
    COUNTRY_GROUPS,
    AID_TYPE_CONFIG,  # Add this
    build_group_allocations_query
)

__all__ = [
    # Functions
    "load_time_series_data",
    "load_country_data",
    "load_data_from_table",
    "build_group_allocations_query",
    
    # Column definitions
    "TOTAL_SUPPORT_COLUMNS",
    "AID_TYPES_COLUMNS",
    "COUNTRY_AID_COLUMNS",
    
    # New constants
    "COUNTRY_GROUPS",
    "AID_TYPE_CONFIG",  # Add this
]