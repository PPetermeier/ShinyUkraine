"""
Main UI configuration.
"""
from shiny import ui
from .pages.timeseries import time_series_page_ui
from .pages.countrywise import country_aid_page_ui

def get_main_ui():
    return ui.page_navbar(
        ui.nav_panel(
            "Over time",
            time_series_page_ui()
        ),
        ui.nav_panel(
            "By Country",
            country_aid_page_ui()
        ),
        title="Ukraine Support Tracker in Shiny",
        id="navigation",
    )