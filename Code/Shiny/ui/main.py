"""Module for main application UI configuration.

This module defines the main navigation structure and page organization
for the Ukraine Support Tracker Shiny application.
"""

from shiny import ui
from typing import Any

from .pages.countrywise import country_aid_page_ui
from .pages.landing import landing_page_ui
from .pages.timeseries import time_series_page_ui
from .pages.financial import financial_page_ui
from .pages.weapons import weapons_page_ui
from .pages.comparisons import comparisons_page_ui
from .pages.about import about_page_ui


def get_main_ui() -> Any:  # Using Any since Shiny's return type isn't easily typed
    """Create the main navigation UI for the application.
    
    This function defines the primary navigation structure of the application,
    organizing different visualization and content pages into a navbar layout.
    
    Returns:
        ui.page_navbar: Main application UI with navigation structure.
    """
    return ui.page_navbar(
        ui.nav_panel("Overview", landing_page_ui()),
        ui.nav_panel("Total Aid over time", time_series_page_ui()),
        ui.nav_panel("Total Aid by country & type", country_aid_page_ui()),
        ui.nav_panel("Financial Aid", financial_page_ui()),
        ui.nav_panel("Weapons", weapons_page_ui()),
        ui.nav_panel("Historic Comparisons", comparisons_page_ui()),
        ui.nav_panel("Text Content", about_page_ui()),
        title="Ukraine Support Tracker in Shiny",
        id="navigation",
        selected="Overview",
    )