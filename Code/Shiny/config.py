"""
Configuration file containing shared constants and settings.
"""

from pathlib import Path

# Get the project root directory (where the top-level repository is)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Database path relative to project root
DB_PATH = PROJECT_ROOT / "Data" / "ukrainesupporttracker.db"


# Plot related
LAST_UPDATE = "2024/08/31"  # For data Transparency in the plots
MARGIN = dict(l=20, r=20, t=80, b=20)

COLOR_PALETTE = {
    # Timeseries EU/US
    "united_states": "#B22234",  # Old Glory Red, from the US Flag
    "europe": "#003399",  # Reflex blue, from the EU Flag
    "other_countries": "#2ECC71",  # Emerald green for total
    # Timeseries by aid types
    "military": "#5A189A",  
    "heavy_weapons_deliveries": "#6932A4" , # Darker purple color for heavy weapons
    "financial": "#FF6700", 
    "humanitarian": "#00CED1", 
    "refugee": "#FFB400",
    "total_bilateral":"#2ECC71",
    'EU_institutions': '#FFCC00',
    'base_color':'#003399',      
    # Commmitments vs. 
    'Australia': '#00008B',      # Dark Blue from Australian flag
    'Austria': '#ED2939',        # Red from Austrian flag
    'Belgium': '#FAE042',        # Yellow from Belgian flag
    'Bulgaria': '#00966E',       # Green from Bulgarian flag
    'Canada': '#FF0000',         # Red from Canadian flag
    'Croatia': '#0093DD',        # Blue from Croatian flag
    'Cyprus': '#D47600',         # Copper color from Cypriot flag
    'Czech Republic': '#11457E',  # Blue from Czech flag
    'Denmark': '#C60C30',        # Red from Danish flag
    'Estonia': '#0072CE',        # Blue from Estonian flag
    'EU (Commission and Council)': '#003399',  # EU Blue
    'Finland': '#002F6C',        # Blue from Finnish flag
    'France': '#0055A4',         # Blue from French flag
    'Germany': '#FFCC00',        # Gold from German flag
    'Greece': '#0D5EAF',         # Blue from Greek flag
    'Hungary': '#CE2939',        # Red from Hungarian flag
    'Iceland': '#02529C',        # Blue from Icelandic flag
    'Ireland': '#169B62',        # Green from Irish flag
    'Italy': '#009246',          # Green from Italian flag
    'Japan': '#BC002D',          # Red from Japanese flag
    'Latvia': '#9E3039',         # Maroon from Latvian flag
    'Lithuania': '#FDB913',      # Yellow from Lithuanian flag
    'Luxembourg': '#00A1DE',     # Light blue from Luxembourg flag
    'Malta': '#CF142B',          # Red from Maltese flag
    'Netherlands': '#FF9B00',    # Dutch Orange
    'New Zealand': '#00247D',    # Blue from New Zealand flag
    'Norway': '#EF2B2D',         # Red from Norwegian flag
    'Poland': '#DC143C',         # Red from Polish flag
    'Portugal': '#006600',       # Green from Portuguese flag
    'South Korea': '#CD2E3A',    # Red from South Korean flag
    'Romania': '#002B7F',        # Blue from Romanian flag
    'Slovakia': '#0B4EA2',       # Blue from Slovak flag
    'Slovenia': '#005CE6',       # Blue from Slovenian flag
    'Spain': '#F1BF00',          # Yellow from Spanish flag
    'Sweden': '#006AA7',         # Blue from Swedish flag
    'Switzerland': '#FF0000',    # Red from Swiss flag
    'Turkey': '#E30A17',         # Red from Turkish flag
    'United Kingdom': '#012169',  # Blue from UK flag
    'United States': '#B22234',  # Red from US flag
    'China': '#DE2910',          # Red from Chinese flag
    'Taiwan': '#FE0000',         # Red from Taiwanese flag
    # Financial bilateral allocations colors
    'financial_grant': '#048BA8',      # Darkest - teal blue
    'financial_swap': '#0DB39E',       # Dark - blue green
    'financial_guarantee': '#16DB93',   # Light - mint
    'financial_loan': '#54E8B9',       # Lightest - pale mint
    'financial_allocations': '#2A9D8F',    # Teal blue, complementary to existing financial colors
    'financial_disbursements': '#264653',   # Dark blue-gray, complementary to existing financial colors
    # Weapon Stocks
    'weapon_stocks_russia': '#E63946',     # Russian red
    'weapon_stocks_prewar': '#457B9D',     # Pre-war blue
    'weapon_stocks_committed': '#E9C46A',   # Committed yellow
    'weapon_stocks_delivered': '#2A9D8F',   # Delivered green
    'weapon_stocks_pending': '#FF9F1C',     # Pending orange
}
