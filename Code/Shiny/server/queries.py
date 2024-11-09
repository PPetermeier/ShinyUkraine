"""
Standardized database query definitions.
"""

# Keep existing column definitions
TOTAL_SUPPORT_COLUMNS = ["month", "united_states_allocated__billion", "europe_allocated__billion"]

AID_TYPES_COLUMNS = [
    "month",
    "military_aid_allocated__billion",
    "military_aid_allocated__billion_without_us",
    "financial_aid_allocated__billion",
    "financial_aid_allocated__billion_without_us",
    "humanitarian_aid_allocated__billion",
]

COUNTRY_AID_COLUMNS = ["country", "financial", "humanitarian", "military", "refugee_cost_estimation"]

GDP_ALLOCATIONS_COLUMNS = ["country", "total_bilateral_allocation", "refugee_cost_estimation"]

ALLOCATIONS_VS_COMMITMENTS_COLUMNS = ["country", "allocated_aid", "committed_aid"]

MAP_SUPPORT_COLUMNS = ["e.country", "l.iso3_code", "e.financial", "e.humanitarian", "e.military", "e.refugee_cost_estimation"]


# Table names
TIME_SERIES_TABLE = "c_allocated_over_time"
COUNTRY_AID_TABLE = "e_allocations_refugees_€"
GDP_ALLOCATIONS_TABLE = "f_bilateral_allocations_gdp_pct"
ALLOCATIONS_VS_COMMITMENTS_TABLE = "d_allocations_vs_commitments"
COUNTRY_LOOKUP_TABLE = "zz_country_lookup"

# New configurations for the aid allocation card
AID_TYPE_CONFIG = {"total": {"label": "Total", "allocated_col": "allocated_aid", "committed_col": "committed_aid"}}
MAP_SUPPORT_TYPES = {
    "military": "Military Support",
    "financial": "Financial Support",
    "humanitarian": "Humanitarian Support",
    "refugee_cost_estimation": "Refugee Support",
}
COUNTRY_GROUPS = {
    "EU_member": "EU Members",
    "EU_institutions": "EU Institutions",
    "Anglosaxon_countries": "Anglo-Saxon Countries",
    "Other_donor_countries": "Other Donors",
}


# Updated map query template
MAP_SUPPORT_QUERY = """
    WITH support_data AS (
        SELECT 
            e.country,
            l.iso3_code,
            {selected_columns},
            ({sum_columns}) as total_support,
            e.gdp_2021,
            CASE 
                WHEN e.gdp_2021 > 0 THEN (({sum_columns}) / e.gdp_2021) * 100
                ELSE 0 
            END as pct_gdp
        FROM "e_allocations_refugees_€" e
        JOIN "zz_country_lookup" l ON e.country = l.country_name
        WHERE l.iso3_code IS NOT NULL
    )
    SELECT *
    FROM support_data
    ORDER BY pct_gdp DESC
"""

GROUP_ALLOCATIONS_QUERY = """
    SELECT 'EU_member' as group_name,
        SUM(COALESCE(a.allocated_aid, 0)) as allocated_aid,
        SUM(COALESCE(a.committed_aid, 0)) as committed_aid
    FROM d_allocations_vs_commitments a
    JOIN zz_country_lookup l ON a.country = l.country_name
    WHERE l.EU_member = TRUE
        AND a.country != 'EU Institutions'
        AND 'EU_member' IN ({group_filter})
    
    UNION ALL
    
    SELECT 'Anglosaxon_countries' as group_name,
        SUM(COALESCE(a.allocated_aid, 0)) as allocated_aid,
        SUM(COALESCE(a.committed_aid, 0)) as committed_aid
    FROM d_allocations_vs_commitments a
    JOIN zz_country_lookup l ON a.country = l.country_name
    WHERE l.Anglosaxon_countries = TRUE
        AND 'Anglosaxon_countries' IN ({group_filter})
    
    UNION ALL
    
    SELECT 'Other_donor_countries' as group_name,
        SUM(COALESCE(a.allocated_aid, 0)) as allocated_aid,
        SUM(COALESCE(a.committed_aid, 0)) as committed_aid
    FROM d_allocations_vs_commitments a
    JOIN zz_country_lookup l ON a.country = l.country_name
    WHERE NOT (l.EU_member OR l.Anglosaxon_countries)
        AND 'Other_donor_countries' IN ({group_filter})
    
    UNION ALL
    
    SELECT 'EU_institutions' as group_name,
        allocated_aid,
        committed_aid
    FROM d_allocations_vs_commitments
    WHERE country = 'EU Institutions'
        AND 'EU_institutions' IN ({group_filter})
    
    ORDER BY allocated_aid DESC"""


def build_group_allocations_query(aid_type, selected_groups):
    """Build the complete query for group allocations."""
    group_filter = ", ".join(f"'{group}'" for group in selected_groups)
    if not group_filter:
        group_filter = "''"

    query = GROUP_ALLOCATIONS_QUERY.format(group_filter=group_filter)
    return query



def build_map_support_query(selected_types):
    """Build query for map visualization with selected aid types."""
    if not selected_types:
        return None
        
    # Build column selections
    selected_columns = [f"e.{aid_type} as {aid_type}" for aid_type in selected_types]
    sum_columns = " + ".join([f"COALESCE({aid_type}, 0)" for aid_type in selected_types])
    
    query = MAP_SUPPORT_QUERY.format(
        selected_columns=", ".join(selected_columns),
        sum_columns=sum_columns
    )
    
    return query
