"""
Main page layout and server coordination.
"""

from shiny import ui

from .cards.aid_types import AidTypesCard, AidTypesServer
from .cards.total_support import TotalSupportCard, TotalSupportServer
from .cards.aid_allocation import AidAllocationCard, AidAllocationServer  # New import

def time_series_page_ui():
    """Return the UI elements for the time series page."""
    return ui.page_fillable(        ui.row(
            ui.column(12, AidAllocationCard.ui()),  # New card
        ui.row(
            ui.column(12, TotalSupportCard.ui())
        ),
        ui.row(
            ui.column(12, AidTypesCard.ui())
        ),

        ),
    )


class TimeSeriesPageServer:
    """Coordinates all cards on the time series page."""

    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session

        # Initialize card servers
        self.total_support = TotalSupportServer(input, output, session)
        self.aid_types = AidTypesServer(input, output, session)
        self.aid_allocation = AidAllocationServer(input, output, session)  # New server

        # Important: Initialize right away
        self.initialize()

    def initialize(self):
        """Initialize all card servers."""
        self.total_support.register_outputs()
        self.aid_types.register_outputs()
        self.aid_allocation.register_outputs()  # New registration