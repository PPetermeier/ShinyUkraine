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

WEAPON_STOCKS_COLUMNS = [
    "country",
    "equipment_type",
    "status",
    "quantity"
]

COUNTRY_AID_COLUMNS = ["country", "financial", "humanitarian", "military", "refugee_cost_estimation"]

GDP_ALLOCATIONS_COLUMNS = ["country", "total_bilateral_allocation", "refugee_cost_estimation"]

ALLOCATIONS_VS_COMMITMENTS_COLUMNS = ["country", "allocated_aid", "committed_aid"]

MAP_SUPPORT_COLUMNS = ["e.country", "l.iso3_code", "e.financial", "e.humanitarian", "e.military", "e.refugee_cost_estimation"]

FINANCIAL_AID_COLUMNS = ["country", "loan", "grant", "guarantee", "central_bank_swap_line"]

BUDGET_SUPPORT_COLUMNS = ["country", "allocations_loans_grants_and_guarantees", "disbursements"]

HEAVY_WEAPONS_COLUMNS = ["country", "tanks", "armored_vehicles", "artillery", "mlrs", "air_defense", "total_deliveries"]

# Table names
TIME_SERIES_TABLE = "c_allocated_over_time"
COUNTRY_AID_TABLE = "e_allocations_refugees_€"
GDP_ALLOCATIONS_TABLE = "f_bilateral_allocations_gdp_pct"
ALLOCATIONS_VS_COMMITMENTS_TABLE = "d_allocations_vs_commitments"
COUNTRY_LOOKUP_TABLE = "zz_country_lookup"
BUDGET_SUPPORT_TABLE = "i_budget_support_by_donor"
FINANCIAL_AID_TABLE = "h_financial_aid_by_type"
WEAPON_STOCKS_BASE_TABLE = "weapon_stocks_base"
WEAPON_STOCKS_DETAIL_TABLE = "weapon_stocks_detail"

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


WEAPON_STOCKS_PREWAR_QUERY = """
    SELECT 
        equipment_type,
        CASE 
            WHEN item LIKE '%Russian%' THEN 'Russia'
            WHEN item LIKE '%Ukrainian%' THEN 'Ukraine'
        END as country,
        quantity
    FROM j_weapon_stocks_base
    WHERE item LIKE '%pre-war%'
    AND quantity IS NOT NULL
"""
WEAPON_STOCK_PLEDGES_QUERY = """
    SELECT 
        m.country,
        m.average_total_delivered as delivered,
        m.average_total_to_be_delivered as to_be_delivered
    FROM m_share_of_stocks_pledged m
    WHERE m.country != 'Average EU' 
    AND m.country != 'Average non-EU-NATO'
    ORDER BY (COALESCE(m.average_total_delivered, 0) + COALESCE(m.average_total_to_be_delivered, 0)) DESC"""


WEAPON_TYPE_PLEDGES_QUERY = """
    SELECT 
        m.country,
        m.tanks as tanks_delivered,
        m."155mm152mm_howitzers" as howitzers_delivered,
        m.mlrs as mlrs_delivered,
        -- Calculate the to-be-delivered amounts
        (m.tanks * (m.average_total_to_be_delivered / NULLIF(m.average_total_delivered, 0))) as tanks_to_deliver,
        (m."155mm152mm_howitzers" * (m.average_total_to_be_delivered / NULLIF(m.average_total_delivered, 0))) as howitzers_to_deliver,
        (m.mlrs * (m.average_total_to_be_delivered / NULLIF(m.average_total_delivered, 0))) as mlrs_to_deliver
    FROM m_share_of_stocks_pledged m
    WHERE m.country != 'Average EU' 
    AND m.country != 'Average non-EU-NATO'
    AND (m.tanks > 0 OR m."155mm152mm_howitzers" > 0 OR m.mlrs > 0)
    ORDER BY (m.average_total_delivered + COALESCE(m.average_total_to_be_delivered, 0)) DESC
"""

WEAPON_STOCKS_SUPPORT_QUERY = """
    SELECT 
        equipment_type,
        status,
        SUM(quantity) as quantity
    FROM (
        SELECT 
            equipment_type,
            CASE 
                WHEN item LIKE '%Delivered%' THEN 'delivered'
                WHEN item LIKE '%be delivered%' THEN 'to_be_delivered'
            END as status,
            quantity
        FROM j_weapon_stocks_base
        WHERE (item LIKE '%Delivered%' OR item LIKE '%be delivered%')
        AND quantity IS NOT NULL
    )
    GROUP BY equipment_type, status
"""

WEAPON_STOCKS_QUERY = """
    SELECT 
        CASE 
            WHEN item LIKE '%Russian%' THEN 'Russia'
            WHEN item LIKE '%Ukrainian%' THEN 'Ukraine'
        END as country,
        equipment_type,
        CASE 
            WHEN item LIKE '%pre-war stock%' THEN 'pre-war'
            WHEN item LIKE '%Committed%' THEN 'committed'
            WHEN item LIKE '%Delivered%' THEN 'delivered'
            WHEN item LIKE '%be delivered%' THEN 'to_be_delivered'
        END as status,
        quantity
    FROM j_weapon_stocks_base
    WHERE quantity IS NOT NULL
        AND equipment_type IS NOT NULL
    ORDER BY 
        equipment_type,
        CASE country 
            WHEN 'Russia' THEN 1
            WHEN 'Ukraine' THEN 2
        END,
        CASE status
            WHEN 'pre-war' THEN 1
            WHEN 'committed' THEN 2
            WHEN 'delivered' THEN 3
            WHEN 'to_be_delivered' THEN 4
        END
"""

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

BUDGET_SUPPORT_QUERY = """
    SELECT 
        country,
        allocations_loans_grants_and_guarantees,
        disbursements
    FROM i_budget_support_by_donor
    WHERE country IS NOT NULL
    ORDER BY allocations_loans_grants_and_guarantees DESC
"""

HEAVY_WEAPONS_DELIVERY_QUERY = """
    SELECT
        country,
        SUM(value_estimates_heavy_weapons) AS value_estimates_heavy_weapons
    FROM g_heavy_weapon_ranking
    GROUP BY country
    ORDER BY value_estimates_heavy_weapons DESC
"""


FINANCIAL_AID_QUERY = """
    SELECT 
        country,
        "loan",
        "grant",
        "guarantee",
        "central_bank_swap_line"
    FROM h_financial_aid_by_type
    WHERE country IS NOT NULL
    ORDER BY (COALESCE("loan", 0) + COALESCE("grant", 0) + 
             COALESCE("guarantee", 0) + COALESCE("central_bank_swap_line", 0)) DESC
"""


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

    query = MAP_SUPPORT_QUERY.format(selected_columns=", ".join(selected_columns), sum_columns=sum_columns)

    return query
