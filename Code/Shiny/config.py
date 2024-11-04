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
    "united_states": "#1E3D59",  # Deep navy blue
    "europe": "#FFC13B",  # Golden yellow
    "total": "#2ECC71",  # Emerald green for total
    # Timeseries by aid types
    "military": "#FF4B4B",  # Red for military aid
    "financial": "#2E86C1",  # Blue for financial aid
    "humanitarian": "#28B463",  # Green for humanitarian aid
    "refugee": "#ff7f0e",
}
