from shiny import ui

from .cards.a_lend_lease import WW2EquipmentComparisonCard, WW2EquipmentComparisonServer
from .cards.b_ww2_values import WW2UkraineComparisonCard, WW2UkraineComparisonServer
from .cards.c_cold_war_values import ColdWarCard, ColdWarServer
from .cards.d_gulf_war_values import GulfWarCard, GulfWarServer
from .cards.e_domestic_priorities import DomesticPrioritiesCard, DomesticPrioritiesServer


def comparisons_page_ui():
    """Return the UI elements for the WW2 comparison page."""
    return ui.page_fillable(
        ui.row(ui.column(12, WW2EquipmentComparisonCard.ui())),
        ui.row(ui.column(12, WW2UkraineComparisonCard.ui())),
        ui.row(ui.column(12, ColdWarCard.ui())),
    ui.row(ui.column(12, GulfWarCard.ui())),
    ui.row(ui.column(12, DomesticPrioritiesCard.ui())),
    )


class ComparisonsPageServer:
    """Coordinates all cards on the WW2 comparison page."""

    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session

        # Initialize card servers
        self.ww2_equipment = WW2EquipmentComparisonServer(input, output, session)
        self.ww_values = WW2UkraineComparisonServer(input, output, session)
        self.cold_war = ColdWarServer(input, output, session)
        self.gulf_war = GulfWarServer(input, output, session)
        self.domestic = DomesticPrioritiesServer(input, output, session)
        # Important: Initialize right away
        self.initialize()

    def initialize(self):
        """Initialize all card servers."""
        self.ww2_equipment.register_outputs()
        self.ww_values.register_outputs()
        self.cold_war.register_outputs()
        self.gulf_war.register_outputs()
        self.domestic.register_outputs()
