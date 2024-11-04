"""
Country aid page layout and server coordination.
"""
from shiny import ui
from .cards.country_aid import CountryAidCard, CountryAidServer

def country_aid_page_ui():
    """Return the UI elements for the country aid page."""
    return ui.page_fillable(
        ui.row(
            ui.column(12, CountryAidCard.ui())
        ),
    )

class CountryAidPageServer:
    """Coordinates all cards on the country aid page."""

    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session

        # Initialize card servers
        self.country_aid = CountryAidServer(input, output, session)

        # Important: Initialize right away
        self.initialize()

    def initialize(self):
        """Initialize all card servers."""
        self.country_aid.register_outputs()