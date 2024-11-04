"""
Time series visualization module containing page layout and server initialization.
"""

from shiny import ui
from ui.pages.timeseries.cards.total_support import TotalSupportCard, TotalSupportServer
from ui.pages.timeseries.cards.aid_types import AidTypesCard, AidTypesServer

def time_series_ui():
    """Return the UI elements for the time series page."""
    return ui.page_fillable(
        ui.row(
            ui.column(
                12, 
                ui.div(
                    {"style": "border: 1px solid blue; margin: 10px;"},
                    ui.h3("Total Support Card"),
                    TotalSupportCard.ui()
                )
            )
        ),
        ui.row(
            ui.column(
                12,
                ui.div(
                    {"style": "border: 1px solid red; margin: 10px;"},
                    ui.h3("Aid Types Card"),
                    AidTypesCard.ui()
                )
            )
        )
    )


class TimeSeriesServer:
    """Server logic for time series visualization page."""

    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
        self.total_support_server = None
        self.aid_types_server = None
        
    def initialize(self):
        """Initialize all card servers."""
        # Initialize total support card server
        self.total_support_server = TotalSupportServer(
            self.input, self.output, self.session
        )
        
        # Initialize aid types card server
        self.aid_types_server = AidTypesServer(
            self.input, self.output, self.session
        )
        
        # Make sure outputs are registered
        if hasattr(self.total_support_server, 'register_outputs'):
            self.total_support_server.register_outputs()
            
        if hasattr(self.aid_types_server, 'register_outputs'):
            self.aid_types_server.register_outputs()