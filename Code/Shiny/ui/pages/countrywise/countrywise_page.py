"""Module for managing the country-wise aid visualization page.

This module coordinates the display and interaction of multiple visualization cards
related to country-specific aid data, including total aid amounts, GDP allocations,
and commitment ratios. It provides both the page layout and server-side coordination
for these components.
"""

from typing import Any, List, Type

from shiny import ui

from .cards.a_country_aid import CountryAidCard, CountryAidServer
from .cards.b_gdp_allocations import GDPAllocationsCard, GDPAllocationsServer
from .cards.c_committment_ratio import CommittmentRatioCard, CommittmentRatioServer


class CountryAidPageLayout:
    """Manages the layout and structure of the country aid page.
    
    This class defines the organization and presentation of visualization cards
    on the country-specific aid data page.
    """

    # Define the cards and their order
    CARD_COMPONENTS: List[Type[Any]] = [
        CountryAidCard,
        GDPAllocationsCard,
        CommittmentRatioCard
    ]

    @staticmethod
    def create_ui() -> ui.page_fillable:
        """Create the user interface for the country aid page.

        Returns:
            ui.page_fillable: A Shiny page containing all country aid-related
                visualization cards arranged in a vertical layout.
        """
        return ui.page_fillable(
            *(
                ui.row(ui.column(12, card_component.ui()))
                for card_component in CountryAidPageLayout.CARD_COMPONENTS
            )
        )


class CountryAidPageServer:
    """Coordinates all visualization cards on the country aid page.
    
    This class manages the server-side components for all country aid-related
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
            'country_aid': CountryAidServer(input, output, session),
            'gdp_allocations': GDPAllocationsServer(input, output, session),
            'commitment_ratio': CommittmentRatioServer(input, output, session)
        }

        self.initialize()

    def initialize(self) -> None:
        """Initialize and register outputs for all card servers."""
        for server in self.servers.values():
            server.register_outputs()


# Create a function to return the UI elements
def country_aid_page_ui() -> ui.page_fillable:
    """Create the UI elements for the country aid page.

    Returns:
        ui.page_fillable: A Shiny page containing all country aid-related
            visualizations.
    """
    return CountryAidPageLayout.create_ui()