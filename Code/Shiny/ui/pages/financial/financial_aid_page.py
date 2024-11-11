# financial_page.py
from shiny import ui

from .cards.financial_by_type import FinancialByTypeCard, FinancialByTypeServer
from .cards.budget_support import BudgetSupportCard, BudgetSupportServer

def financial_page_ui():
    """Return the UI elements for the financial aid page."""
    return ui.page_fillable(
        ui.row(
            ui.column(12, FinancialByTypeCard.ui())
        ),
        ui.row(
            ui.column(12, BudgetSupportCard.ui())
        )
    )

class FinancialPageServer:
    """Coordinates all cards on the financial aid page."""

    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session

        # Initialize card servers
        self.financial_by_type = FinancialByTypeServer(input, output, session)
        self.budget_support = BudgetSupportServer(input, output, session)

        # Important: Initialize right away
        self.initialize()

    def initialize(self):
        """Initialize all card servers."""
        self.financial_by_type.register_outputs()
        self.budget_support.register_outputs()