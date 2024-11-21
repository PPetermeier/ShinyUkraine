"""Module for managing the historical comparisons page.

This module coordinates the display and interaction of multiple visualization cards
comparing Ukraine support with historical military aid and domestic spending programs.
It provides both the page layout and server-side coordination for these components,
including WW2 equipment comparisons, Cold War values, Gulf War comparisons, and
domestic priorities.
"""

from typing import Any, List, Type

from shiny import ui

from .cards.a_lend_lease import WW2EquipmentComparisonCard, WW2EquipmentComparisonServer
from .cards.b_ww2_values import WW2UkraineComparisonCard, WW2UkraineComparisonServer
from .cards.c_cold_war_values import ColdWarCard, ColdWarServer
from .cards.d_gulf_war_values import GulfWarCard, GulfWarServer
from .cards.e_domestic_priorities import DomesticPrioritiesCard, DomesticPrioritiesServer


class ComparisonsPageLayout:
    """Manages the layout and structure of the comparisons page.
    
    This class defines the organization and presentation of visualization cards
    on the historical comparisons page.
    """

    # Define the cards and their order
    CARD_COMPONENTS: List[Type[Any]] = [
        WW2EquipmentComparisonCard,
        WW2UkraineComparisonCard,
        ColdWarCard,
        GulfWarCard,
        DomesticPrioritiesCard
    ]

    @staticmethod
    def create_ui() -> ui.page_fillable:
        """Create the user interface for the comparisons page.

        Returns:
            ui.page_fillable: A Shiny page containing all comparison-related
                visualization cards arranged in a vertical layout.
        """
        return ui.page_fillable(
            *(
                ui.row(ui.column(12, card_component.ui()))
                for card_component in ComparisonsPageLayout.CARD_COMPONENTS
            )
        )


class ComparisonsPageServer:
    """Coordinates all visualization cards on the comparisons page.
    
    This class manages the server-side components for all comparison-related
    visualizations, handling their initialization and coordination.

    Attributes:
        input: Shiny input object containing user interface values.
        output: Shiny output object for rendering visualizations.
        session: Shiny session object.
        servers: Dictionary of initialized card servers.
    """

    def __init__(self, input: Any, output: Any, session: Any):
        """Initialize the page server and all card servers.

        Args:
            input: Shiny input object.
            output: Shiny output object.
            session: Shiny session object.
        """
        self.input = input
        self.output = output
        self.session = session

        # Initialize all card servers
        self.servers = {
            'ww2_equipment': WW2EquipmentComparisonServer(input, output, session),
            'ww2_values': WW2UkraineComparisonServer(input, output, session),
            'cold_war': ColdWarServer(input, output, session),
            'gulf_war': GulfWarServer(input, output, session),
            'domestic': DomesticPrioritiesServer(input, output, session)
        }

        self.initialize()

    def initialize(self) -> None:
        """Initialize and register outputs for all card servers."""
        for server in self.servers.values():
            server.register_outputs()


# Create a function to return the UI elements
def comparisons_page_ui() -> ui.page_fillable:
    """Create the UI elements for the comparisons page.

    Returns:
        ui.page_fillable: A Shiny page containing all comparison-related
            visualizations.
    """
    return ComparisonsPageLayout.create_ui()