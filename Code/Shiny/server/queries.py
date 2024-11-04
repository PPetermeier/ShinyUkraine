"""
Standardized database query definitions.
"""

# Time series data columns
TOTAL_SUPPORT_COLUMNS = [
    "month",
    "united_states_allocated__billion",
    "europe_allocated__billion"
]

AID_TYPES_COLUMNS = [
    "month",
    "military_aid_allocated__billion",
    "military_aid_allocated__billion_without_us",
    "financial_aid_allocated__billion",
    "financial_aid_allocated__billion_without_us",
    "humanitarian_aid_allocated__billion"
]

# Country aid data columns
COUNTRY_AID_COLUMNS = [
    "country",
    "financial",
    "humanitarian",
    "military",
    "refugee_cost_estimation"
]

# Table names
TIME_SERIES_TABLE = "c_allocated_over_time"
COUNTRY_AID_TABLE = "e_allocations_refugees_€"