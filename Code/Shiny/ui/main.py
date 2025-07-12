"""Module for main application UI configuration.

This module defines the main navigation structure and page organization
for the Ukraine Support Tracker Shiny application.
"""

from typing import Any

from shiny import ui

from .pages.a_landing import landing_page_ui
from .pages.b_map import map_page_ui
from .pages.c_timeseries import time_series_page_ui
from .pages.d_countrywise import country_aid_page_ui
from .pages.e_financial import financial_page_ui
from .pages.f_weapons import weapons_page_ui
from .pages.g_comparisons import comparisons_page_ui


def get_main_ui() -> Any:  # Using Any since Shiny's return type isn't easily typed
    """Create the main navigation UI for the application.

    This function defines the primary navigation structure of the application,
    organizing different visualization and content pages into a navbar layout.

    Returns:
        ui.page_navbar: Main application UI with navigation structure.
    """
    return ui.page_navbar(
        ui.nav_panel("Landing", landing_page_ui()),
        ui.nav_panel("Map: Types, abs & rel", map_page_ui()),
        ui.nav_panel("Timeseries", time_series_page_ui()),
        ui.nav_panel("By Country & Type", country_aid_page_ui()),
        ui.nav_panel("Financial Aid", financial_page_ui()),
        ui.nav_panel("Weapon Deliveries", weapons_page_ui()),
        ui.nav_panel("Historic Comparisons", comparisons_page_ui()),
        title="Ukraine Support Tracker in Shiny",
        id="navigation",
        selected="Landing",
    )
