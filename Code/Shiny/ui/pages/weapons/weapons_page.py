
from shiny import ui

from .cards.heavy_weapons import HeavyWeaponsCard, HeavyWeaponsServer

def heavy_weapons_page_ui():
    """Return the UI elements for the heavy weapons page."""
    return ui.page_fillable(
        ui.row(
            ui.column(12, HeavyWeaponsCard.ui())
        )
    )

class HeavyWeaponsPageServer:
    """Coordinates all cards on the heavy weapons page."""

    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session

        # Initialize card server
        self.heavy_weapons = HeavyWeaponsServer(input, output, session)

        # Important: Initialize right away
        self.initialize()

    def initialize(self):
        """Initialize all card servers."""
        self.heavy_weapons.register_outputs()