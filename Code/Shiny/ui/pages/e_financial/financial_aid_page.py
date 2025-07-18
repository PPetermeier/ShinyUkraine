"""Module for managing the financial aid visualization page.

This module coordinates the display and interaction of visualization cards related
to financial aid data, including breakdowns by type and budget support. It provides
both the page layout and server-side coordination for these components.
"""

from typing import Any

from shiny import ui

from .cards.a_financial_by_type import FinancialByTypeCard, FinancialByTypeServer
from .cards.b_budget_support import BudgetSupportCard, BudgetSupportServer


class FinancialPageLayout:
    """Manages the layout and structure of the financial aid page.

    This class defines the organization and presentation of visualization cards
    on the financial aid data page.
    """

    # Define the cards and their order
    CARD_COMPONENTS: list[type[Any]] = [FinancialByTypeCard, BudgetSupportCard]

    @staticmethod
    def create_ui() -> ui.page_fillable:
        """Create the user interface for the financial aid page.

        Returns:
            ui.page_fillable: A Shiny page containing all financial aid-related
                visualization cards arranged in a vertical layout.
        """
        return ui.page_fillable(
            *(
                ui.row(ui.column(12, card_component.ui()))
                for card_component in FinancialPageLayout.CARD_COMPONENTS
            )
        )


class FinancialPageServer:
    """Coordinates all visualization cards on the financial aid page.

    This class manages the server-side components for all financial aid-related
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
            "financial_by_type": FinancialByTypeServer(input, output, session),
            "budget_support": BudgetSupportServer(input, output, session),
        }

        self.initialize()

    def initialize(self) -> None:
        """Initialize and register outputs for all card servers."""
        for server in self.servers.values():
            server.register_outputs()


# Create a function to return the UI elements
def financial_page_ui() -> ui.page_fillable:
    """Create the UI elements for the financial aid page.

    Returns:
        ui.page_fillable: A Shiny page containing all financial aid-related
            visualizations.
    """
    return FinancialPageLayout.create_ui()
