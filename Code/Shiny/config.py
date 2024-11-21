"""
Configuration file containing shared constants and settings.
"""
import os

DB_PATH = os.path.join(os.getcwd(), "Data", "ukrainesupporttracker.db")


# Plot related
LAST_UPDATE = "2024/08/31"  # For data Transparency in the plots
MARGIN = dict(l=20, r=20, t=80, b=20)
COMPARISONS_MARGIN = dict(t=200, l=50, r=50, b=50)

COLOR_PALETTE = {
    # Timeseries EU/US
    "united_states": "#A83B4C",
    "United States": "#A83B4C",
    "Ukraine Map": "#B22222",
    "europe": "#3957A7",
    "Europe": "#3957A7",
    "EU Institutions": "#D1A23A",
    "Other Countries": "#6A5D8C",
    "other_donors": "#6A5D8C",
    # Timeseries by aid types
    "military": "#6B8E23",
    "financial": "#048BA8",
    "humanitarian": "#FFA500",
    "refugee": "#0072BC",
    "Total Bilateral": "#2E8B57",
    "base_color": "#003399",
    # Commmitments vs.
    # Financial bilateral allocations colors
    "aid_committed": "#D8A769",
    "aid_delivered": "#7386C1",
    # Financial aid page
    "financial_grant": "#048BA8",  # Darkest - teal blue
    "financial_swap": "#0DB39E",  # Dark - blue green
    "financial_guarantee": "#16DB93",  # Light - mint
    "financial_loan": "#54E8B9",  # Lightest - pale mint
    "financial_allocations": "#2A9D8F",  # Teal blue, complementary to existing financial colors
    "financial_disbursements": "#264653",  # Dark blue-gray, complementary to existing financial colors

    # Weapon Stocks
    "weapon_stocks_russia": "#E63946",  # Russian red
    "weapon_stocks_prewar": "#457B9D",  # Pre-war blue
    "weapon_stocks_committed": "#E9C46A",  # Committed yellow
    "weapon_stocks_delivered": "#2A9D8F",  # Delivered green
    "weapon_stocks_pending": "#FF9F1C",  # Pending orange

    # Lend-Lease
    "WW2 lend-lease US total delivered": "#A83B4C",
    "US to Great Britain (1941-45)":"#601757",
    "US to USSR (1941-45)": "#551A8B",
    "Spain (1936-39) Nationalists":"#00247D",
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
    "British to Ukraine": " #807E3F",

    # Cold War values
    "US in Korea (average mil. exp. 1950-53)": "#a83b4c",  
    "US in Vietnam (average mil. exp. 1965-75)": "#b9626f",  
    "US in Iraq (average mil. exp. 2003-2010)": "#ca8993", 
    "US in Afghanistan (average mil. exp. 2001-10)": "#dcb0b7",
    "US to Ukraine (total military aid)": "#E89B5D",
    # Gulf War Values
    "Gulf War Percentage": "#9A6FB8",
    # Crisis Comparisons
    #   Europe
    "Eurozone bailouts \n(2010-2012)": "#00CED1",
    "EU pandemic recover fund\n (Next Generation EU)": "#4B0082",
    "EU support to Ukraine": "#FFD700",
    #   Domestic
    "Aid for Ukraine (incl. EU share)": "#FFD700",
    "Fiscal commitments for energy subsidies": "#FF8C59",
    # 98FB98 (Pale Green)
    # 00FA9A (Medium Spring Green)
    # 32CD32 (Lime Green)
    # DAA520 (Golden Rod)
    # D3D3D3 (Light Gray)
    # F0E68C (Khaki)
    #   Germany
    'Energy subsidies for households and firms ("Doppelwumms")': "#FF8C59",
    'Special military fund ("Sondervermögen Bundeswehr") ': "#CB59FF",
    "German aid to Ukraine": "#FFD700",
    "Rescue of Uniper (incl. EU shares)": "#59ADFF",
    'Transport Subsidies ("Tankrabatt" & "9€ Ticket")': "#357899",
}
