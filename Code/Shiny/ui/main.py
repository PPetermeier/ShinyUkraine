"""
Main UI configuration.
"""
from shiny import ui

from .pages.countrywise import country_aid_page_ui
from .pages.landing import landing_page_ui
from .pages.timeseries import time_series_page_ui
from .pages.financial import financial_page_ui
from .pages.weapons import heavy_weapons_page_ui  
from .pages.comparisons import comparisons_page_ui
from .pages.about import about_page_ui

def get_main_ui():
    return ui.page_navbar(
        ui.nav_panel("Overview", landing_page_ui()),
        ui.nav_panel("Total Aid over time", time_series_page_ui()),
        ui.nav_panel("Total Aid by country & type", country_aid_page_ui()),
        ui.nav_panel("Financial Aid", financial_page_ui()),
        ui.nav_panel("Weapons", heavy_weapons_page_ui()),
        ui.nav_panel("Historic Comparisons", comparisons_page_ui()),
        ui.nav_panel("Text Content", about_page_ui()),
        title="Ukraine Support Tracker in Shiny",
        id="navigation",
        selected="Overview",
    )