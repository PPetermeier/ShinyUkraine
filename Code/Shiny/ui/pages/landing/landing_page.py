"""
Main page layout and server coordination for map visualization.
"""

from shiny import ui

from .map_card import MapCard, MapServer


def landing_page_ui():
    """Return the UI elements for the map page."""
    return ui.page_fillable(
        ui.div(
            {"class": "container-fluid"},
            ui.div(
                {"class": "row mb-4"},
                ui.div(
                    {"class": "col-12"},
                    ui.h2("Global Support for Ukraine", class_="mb-3"),
                    ui.markdown(
                        """
                        This tracker provides a comprehensive overview of the support provided to Ukraine
                        by partner countries since Russia's invasion in February 2022. The data includes
                        bilateral commitments of financial, humanitarian, military support and support
                        for refugees from government sources.
                        
                        The visualization below shows the total amount of support by country across
                        different aid categories. You can select specific types of support using the
                        controls in the sidebar. All values are in billion euros.
                        
                        **Note:** The data includes:
                        - Military: Direct military aid and military-purposed financial aid
                        - Financial: Direct financial aid excluding military purposes
                        - Humanitarian: Direct humanitarian assistance
                        - Refugee: Support for Ukrainian refugees in host countries
                        """
                    ),
                ),
            ),
            ui.div(
                {"class": "row"},
                ui.div({"class": "col-12"}, MapCard.ui()),
            ),
        ),
    )


class LandingPageServer:
    """Coordinates all components on the map page."""

    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session

        # Initialize card server
        self.map_card = MapServer(input, output, session)

        # Important: Initialize right away
        self.initialize()

    def initialize(self):
        """Initialize all components."""
        self.map_card.register_outputs()
