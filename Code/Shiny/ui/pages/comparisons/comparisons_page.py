from shiny import ui

from .cards.lend_lease import WW2EquipmentComparisonCard, WW2EquipmentComparisonServer

def comparisons_page_ui():
    """Return the UI elements for the WW2 comparison page."""
    return ui.page_fillable(
        ui.row(
            ui.column(12, WW2EquipmentComparisonCard.ui())
        )
    )

class ComparisonsPageServer:
    """Coordinates all cards on the WW2 comparison page."""

    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session

        # Initialize card servers
        self.ww2_equipment = WW2EquipmentComparisonServer(input, output, session)

        # Important: Initialize right away
        self.initialize()

    def initialize(self):
        """Initialize all card servers."""
        self.ww2_equipment.register_outputs()