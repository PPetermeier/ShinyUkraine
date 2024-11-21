"""Main application module for the Ukraine Support Tracker.

This module initializes and configures the main Shiny application, setting up
all page servers and connecting them to the UI components.
"""

from typing import Any

from shiny import App, Session
from ui import get_main_ui
from ui.pages.d_countrywise import CountryAidPageServer
from ui.pages.b_map import MapPageServer
from ui.pages.timeseries import TimeSeriesPageServer
from ui.pages.financial import FinancialPageServer
from ui.pages.weapons import WeaponsPageServer
from ui.pages.comparisons import ComparisonsPageServer
from ui.pages.a_landing import LandingPageServer


def server(input: Any, output: Any, session: Session) -> None:
    """Initialize and configure all page servers for the application.

    This function sets up server-side logic for each page in the application,
    connecting data processing and visualization components to their respective
    UI elements.

    Args:
        input: Shiny input object containing user interface values.
        output: Shiny output object for rendering visualizations.
        session: Shiny session object for managing application state.
    """
    # Initialize page servers
    servers = [
        LandingPageServer(input, output, session),
        MapPageServer(input, output, session),
        TimeSeriesPageServer(input, output, session),
        CountryAidPageServer(input, output, session),
        FinancialPageServer(input, output, session),
        WeaponsPageServer(input, output, session),
        ComparisonsPageServer(input, output, session),
    ]

    # Initialize all servers
    for server in servers:
        server.initialize()


# Create the Shiny application instance
app = App(get_main_ui(), server)
