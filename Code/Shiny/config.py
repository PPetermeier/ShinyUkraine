"""Configuration module for the Ukraine Support Tracker.

This module provides centralized configuration settings and constants used
throughout the application, including file paths, visualization settings,
and color palettes for different types of visualizations.
"""

import os

# Database configuration
DB_PATH: str = os.path.join(os.getcwd(), "Data", "ukrainesupporttracker.db")

# Plot configuration
LAST_UPDATE: str = "2024/08/31"
MARGIN: dict[str, int] = dict(l=20, r=20, t=80, b=20)
COMPARISONS_MARGIN: dict[str, int] = dict(t=200, l=50, r=50, b=50)

# Color palette configuration
ColorType = dict[str, str]

# Color palette organized by visualization category
TIMESERIES_COLORS: ColorType = {
    "united_states": "#A83B4C",
    "United States": "#A83B4C",
    "Ukraine Map": "#B22222",
    "europe": "#3957A7",
    "Europe": "#3957A7",
    "EU Institutions": "#D1A23A",
    "Other Countries": "#6A5D8C",
    "other_donors": "#6A5D8C",
}

AID_TYPE_COLORS: ColorType = {
    "military": "#6B8E23",
    "financial": "#048BA8",
    "humanitarian": "#FFA500",
    "refugee": "#0072BC",
    "Total Bilateral": "#2E8B57",
    "base_color": "#003399",
}

COMMITMENT_COLORS: ColorType = {
    "aid_committed": "#D8A769",
    "aid_delivered": "#7386C1",
}

FINANCIAL_COLORS: ColorType = {
    "financial_grant": "#048BA8",
    "financial_swap": "#0DB39E",
    "financial_guarantee": "#16DB93",
    "financial_loan": "#54E8B9",
    "financial_allocations": "#2A9D8F",
    "financial_disbursements": "#264653",
}

WEAPON_STOCK_COLORS: ColorType = {
    "weapon_stocks_russia": "#E63946",
    "weapon_stocks_prewar": "#457B9D",
    "weapon_stocks_committed": "#E9C46A",
    "weapon_stocks_delivered": "#2A9D8F",
    "weapon_stocks_pending": "#FF9F1C",
}

HISTORICAL_COMPARISON_COLORS: ColorType = {
    # Lend-Lease
    "WW2 lend-lease US total delivered": "#A83B4C",
    "US to Great Britain (1941-45)": "#601757",
    "US to USSR (1941-45)": "#551A8B",
    "Spain (1936-39) Nationalists": "#00247D",
    "Spain (1936-39) Republicans": "#4682B4",
    "Total supply to Ukraine": "#FFD700",
    # WW2 Values
    "WW2 US to UK": "#601757",
    "WW2 US to USSR": "#551A8B",
    "Spain Nationalists": "#00247D",
    "WW2 British to USSR": "#FF6C00",
    "WW2 UK UDSSR": "#80123F",
    "WW2 US to France": "#80AAD2",
    "US to Ukraine": "#E89B5D",
    "British to Ukraine": "#807E3F",
}

MODERN_CONFLICT_COLORS: ColorType = {
    # Cold War values
    "US in Korea (average mil. exp. 1950-53)": "#a83b4c",
    "US in Vietnam (average mil. exp. 1965-75)": "#b9626f",
    "US in Iraq (average mil. exp. 2003-2010)": "#ca8993",
    "US in Afghanistan (average mil. exp. 2001-10)": "#dcb0b7",
    "US to Ukraine (total military aid)": "#E89B5D",
    # Gulf War Values
    "Gulf War Percentage": "#9A6FB8",
}

CRISIS_COMPARISON_COLORS: ColorType = {
    # Europe
    "Eurozone bailouts \n(2010-2012)": "#00CED1",
    "EU pandemic recover fund\n (Next Generation EU)": "#4B0082",
    "EU support to Ukraine": "#FFD700",
    # Domestic
    "Aid for Ukraine (incl. EU share)": "#FFD700",
    "Fiscal commitments for energy subsidies": "#FF8C59",
    # Germany
    'Energy subsidies for households and firms ("Doppelwumms")': "#FF8C59",
    'Special military fund ("Sondervermögen Bundeswehr") ': "#CB59FF",
    "German aid to Ukraine": "#FFD700",
    "Rescue of Uniper (incl. EU shares)": "#59ADFF",
    'Transport Subsidies ("Tankrabatt" & "9€ Ticket")': "#357899",
}

# Combined color palette for backward compatibility
COLOR_PALETTE: ColorType = {
    **TIMESERIES_COLORS,
    **AID_TYPE_COLORS,
    **COMMITMENT_COLORS,
    **FINANCIAL_COLORS,
    **WEAPON_STOCK_COLORS,
    **HISTORICAL_COMPARISON_COLORS,
    **MODERN_CONFLICT_COLORS,
    **CRISIS_COMPARISON_COLORS,
}
