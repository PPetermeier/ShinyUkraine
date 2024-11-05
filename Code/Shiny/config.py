"""
Configuration file containing shared constants and settings.
"""

from pathlib import Path

# Get the project root directory (where the top-level repository is)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Database path relative to project root
DB_PATH = PROJECT_ROOT / "Data" / "ukrainesupporttracker.db"


COLOR_PALETTE = {
    # Timeseries EU/US
    "united_states": "#B22234",  # Old Glory Red, from the US Flag
    "europe": "#003399",  # Reflex blue, from the EU Flag
    "total": "#2ECC71",  # Emerald green for total
    # Timeseries by aid types
    "military": "#5A189A",  # Red for military aid
    "financial": "#FF6700",  # Blue for financial aid
    "humanitarian": "#00CED1",  # Green for humanitarian aid
    "refugee": "#FFB400",
}
