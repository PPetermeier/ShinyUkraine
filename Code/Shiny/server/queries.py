"""Standardized database query definitions."""

# Keep existing column definitions
TOTAL_SUPPORT_COLUMNS = [
    "month",
    "united_states_allocated__billion",
    "europe_allocated__billion",
    "other_donors_allocated__billion",
]

AID_TYPES_COLUMNS = [
    "month",
    "military_aid_allocated__billion",
    "military_aid_allocated__billion_without_us",
    "financial_aid_allocated__billion",
    "financial_aid_allocated__billion_without_us",
    "humanitarian_aid_allocated__billion",
]

WEAPON_STOCKS_COLUMNS = ["country", "equipment_type", "status", "quantity"]

COUNTRY_AID_COLUMNS = [
    "country",
    "financial",
    "humanitarian",
    "military",
    "refugee_cost_estimation",
]

GDP_ALLOCATIONS_COLUMNS = [
    "country",
    "total_bilateral_allocation",
    "refugee_cost_estimation",
]

ALLOCATIONS_VS_COMMITMENTS_COLUMNS = ["country", "allocated_aid", "committed_aid"]

MAP_SUPPORT_COLUMNS = [
    "e.country",
    "l.iso3_code",
    "e.financial",
    "e.humanitarian",
    "e.military",
    "e.refugee_cost_estimation",
]

FINANCIAL_AID_COLUMNS = [
    "country",
    "loan",
    "grant",
    "guarantee",
    "central_bank_swap_line",
]

BUDGET_SUPPORT_COLUMNS = [
    "country",
    "allocations_loans_grants_and_guarantees",
    "disbursements",
]

HEAVY_WEAPONS_COLUMNS = [
    "country",
    "tanks",
    "armored_vehicles",
    "artillery",
    "mlrs",
    "air_defense",
    "total_deliveries",
]

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
AID_TYPE_CONFIG = {
    "total": {
        "label": "Total",
        "allocated_col": "allocated_aid",
        "committed_col": "committed_aid",
    }
}
MAP_SUPPORT_TYPES = {
    "military": "Military Support",
    "financial": "Financial Support",
    "humanitarian": "Humanitarian Support",
    "refugee_cost_estimation": "Refugee Cost Estimation",
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

WW2_WEAPON_CATEGORIES = {
    "heavy": ["Tanks"],
    "artillery": ["Artillery", "Howitzer(155/152mm)", "MLRS"],
    "air": ["Combat Aircraft"],
}

WW2_CONFLICTS = [
    "WW2 lend-lease US total delivered",
    "US to Great Britain (1941-45)",
    "US to USSR (1941-45)",
    "Spain (1936-39) Nationalists",
    "Spain (1936-39) Republicans",
    "Total supply to Ukraine",
]

# Base query for WW2 comparisons
WW2_EQUIPMENT_BASE_QUERY = """
    SELECT 
        military_conflict,
        weapon_type,
        delivered,
        to_be_delivered
    FROM n_comparison_spain_ww2_equipment
    WHERE military_conflict IN ({conflicts})
"""


# Query with category grouping
WW2_EQUIPMENT_CATEGORIZED_QUERY = """
    WITH base_data AS (
        SELECT 
            CASE 
                WHEN military_conflict LIKE 'WW2 lend-lease US total%' THEN 'WW2 lend-lease US total delivered'
                WHEN military_conflict LIKE 'US to Great Britain%' THEN 'US to Great Britain (1941-45)'
                WHEN military_conflict LIKE 'US to USSR%' THEN 'US to USSR (1941-45)'
                WHEN military_conflict LIKE 'Spain (1936-39) Nationalists%' THEN 'Spain (1936-39) Nationalists'
                WHEN military_conflict LIKE 'Spain (1936-39) Republicans%' THEN 'Spain (1936-39) Republicans'
                WHEN military_conflict LIKE 'Total supply to Ukraine%' THEN 'Total supply to Ukraine'
            END as military_conflict,
            TRIM(weapon_type) as weapon_type,
            delivered,
            COALESCE(to_be_delivered, 0) as to_be_delivered,
            CASE 
                WHEN TRIM(weapon_type) = 'Tanks' THEN 'heavy'
                WHEN TRIM(weapon_type) IN ('Artillery', 'Howitzer(155/152mm)', 'MLRS') THEN 'artillery'
                WHEN TRIM(weapon_type) = 'Combat Aircraft' THEN 'air'
            END as category
        FROM n_comparison_spain_ww2_equipment
        WHERE military_conflict IS NOT NULL
    )
    SELECT 
        military_conflict,
        category,
        weapon_type,
        SUM(delivered) as delivered,
        SUM(to_be_delivered) as to_be_delivered
    FROM base_data
    WHERE category IS NOT NULL
        AND military_conflict IS NOT NULL
    GROUP BY military_conflict, category, weapon_type
    ORDER BY 
        CASE military_conflict
            WHEN 'WW2 lend-lease US total delivered' THEN 1
            WHEN 'US to Great Britain (1941-45)' THEN 2
            WHEN 'US to USSR (1941-45)' THEN 3
            WHEN 'Spain (1936-39) Nationalists' THEN 4
            WHEN 'Spain (1936-39) Republicans' THEN 5
            WHEN 'Total supply to Ukraine' THEN 6
        END,
        category,
        weapon_type
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

WW2_COMPARISON_QUERY = """
    SELECT 
        gdp.military_support,
        gdp.military_conflict,
        gdp.military_aid__of_donor_gdp as gdp_share,
        abs.military_aid_billion_euros as absolute_value
    FROM o_comparison_ww2_gdp gdp
    JOIN p_comparison_ww2_abs abs 
        ON gdp.military_support = abs.military_support 
        AND gdp.military_conflict = abs.military_conflict
    ORDER BY 
        CASE 
            WHEN gdp.military_support LIKE '%UK%1941%' THEN 1
            WHEN gdp.military_support LIKE '%USSR%1941%' THEN 2
            WHEN gdp.military_support LIKE '%France%1941%' THEN 3
            WHEN gdp.military_support LIKE '%Ukraine%' THEN 4
        END
"""

US_WARS_COMPARISON_QUERY = """
    SELECT 
        gdp.military_support,
        gdp.military_conflict,
        gdp.military_aid__of_donor_gdp as gdp_share,
        abs.military_aid_billion_euros as absolute_value
    FROM q_comparison_us_wars_gdp gdp
    JOIN r_comparison_us_wars_abs abs 
        ON gdp.military_support = abs.military_support 
        AND gdp.military_conflict = abs.military_conflict
    ORDER BY 
        CASE 
            WHEN gdp.military_support LIKE '%Korea%' THEN 1
            WHEN gdp.military_support LIKE '%Vietnam%' THEN 2
            WHEN gdp.military_support LIKE '%Iraq%' THEN 3
            WHEN gdp.military_support LIKE '%Afghanistan%' THEN 4
            WHEN gdp.military_support LIKE '%Ukraine%' THEN 5
        END
"""
GULF_WAR_COMPARISON_QUERY = """
    SELECT 
        gdp.countries,
        gdp.gulf_war_199091 as gulf_war_gdp,
        gdp.aid_to_ukraine__of_donor_gdp as ukraine_gdp,
        abs.gulf_war_199091 as gulf_war_abs,
        abs.aid_to_ukraine_billion_euros as ukraine_abs
    FROM s_comparison_gulf_war_gdp gdp
    JOIN t_comparison_gulf_war_abs abs 
        ON gdp.countries = abs.countries
    ORDER BY 
        CASE 
            WHEN gdp.countries = 'United States' THEN 1
            WHEN gdp.countries = 'Germany' THEN 2
            WHEN gdp.countries = 'Japan' THEN 3
            WHEN gdp.countries = 'South Korea' THEN 4
        END
"""

DOMESTIC_COMPARISON_QUERY = """
    SELECT 
        gdp.countries,
        gdp.fiscal_commitments_for_energy_subsidies as fiscal_gdp,
        gdp.aid_for_ukraine_incl_eu_shares as ukraine_gdp,
        abs.fiscal_commitments_for_energy_subsidies as fiscal_abs,
        abs.aid_for_ukraine_incl_eu_share as ukraine_abs
    FROM w_comparison_domestic_gdp gdp
    JOIN v_comparison_domestic_abs abs 
        ON gdp.countries = abs.countries
    ORDER BY 
        CASE 
            WHEN gdp.countries = 'Germany' THEN 1
            WHEN gdp.countries = 'United Kingdom' THEN 2
            WHEN gdp.countries = 'Italy' THEN 3
            WHEN gdp.countries = 'France' THEN 4
            WHEN gdp.countries = 'Spain' THEN 5
            WHEN gdp.countries = 'Netherlands' THEN 6
            WHEN gdp.countries = 'EU average' THEN 7
        END
"""
EUROPEAN_CRISIS_QUERY = """
    SELECT 
        commitments,
        total_support__billion
    FROM u_comparison_european_crises
    ORDER BY 
        CASE 
            WHEN commitments LIKE '%pandemic%' THEN 1
            WHEN commitments LIKE '%Eurozone%' THEN 2
            WHEN commitments LIKE '%Ukraine%' THEN 3
        END
"""

GERMAN_COMPARISON_QUERY = """
    SELECT 
        commitments,
        commitments_1 as description,
        total_bilateral_aid,
        eu_aid_shares,
        cost
    FROM x_comparison_germany_abs
    ORDER BY 
        CASE 
            WHEN commitments LIKE '%Energy%' THEN 1
            WHEN commitments LIKE '%Special military%' THEN 2
            WHEN commitments LIKE '%German aid%' THEN 3
            WHEN commitments LIKE '%Rescue%' THEN 4
            WHEN commitments LIKE '%Transport%' THEN 5
        END
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
    sum_columns = " + ".join(
        [f"COALESCE({aid_type}, 0)" for aid_type in selected_types]
    )

    query = MAP_SUPPORT_QUERY.format(
        selected_columns=", ".join(selected_columns), sum_columns=sum_columns
    )

    return query
