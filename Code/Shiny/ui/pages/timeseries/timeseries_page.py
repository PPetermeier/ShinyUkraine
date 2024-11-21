"""Time series visualization module for the Ukraine Support Tracker.

This module defines the time series analysis page layout and server coordination.
It manages multiple visualization cards showing temporal patterns in aid distribution,
including total support trends, aid type breakdowns, and allocation patterns over time.

The page provides interactive visualizations that help users understand how support
for Ukraine has evolved since the invasion, broken down by different metrics and
categories.
"""

from typing import Any

from shiny import Session, ui


from .cards.aid_allocation import AidAllocationCard, AidAllocationServer
from .cards.aid_types import AidTypesCard, AidTypesServer
from .cards.total_support import TotalSupportCard, TotalSupportServer


def time_series_page_ui() -> ui.page_fillable:
    """Create the user interface elements for the time series page.

    Returns:
        ui.Page: A Shiny page containing multiple visualization cards arranged
            in a vertical layout.
    """
    return ui.page_fillable(
        ui.div(
            {"class": "container-fluid"},
            _create_header_section(),
            _create_visualization_layout(),
        )
    )


def _create_visualization_layout() -> ui.Tag:
    """Create the layout structure for the visualization cards.

    Returns:
        ui.Tag: A div containing the arranged visualization cards.
    """
    return ui.div(
        {"class": "row g-4"},
        _create_aid_allocation_section(),
        _create_total_support_section(),
        _create_aid_types_section(),
    )


def _create_aid_allocation_section() -> ui.Tag:
    """Create the section containing the aid allocation visualization.

    Returns:
        ui.Tag: A column containing the aid allocation card.
    """
    return ui.div(
        {"class": "col-12"},
        AidAllocationCard.ui(),
    )


def _create_total_support_section() -> ui.Tag:
    """Create the section containing the total support visualization.

    Returns:
        ui.Tag: A column containing the total support card.
    """
    return ui.div(
        {"class": "col-12"},
        TotalSupportCard.ui(),
    )


def _create_aid_types_section() -> ui.Tag:
    """Create the section containing the aid types visualization.

    Returns:
        ui.Tag: A column containing the aid types card.
    """
    return ui.div(
        {"class": "col-12"},
        AidTypesCard.ui(),
    )


def _create_header_section() -> ui.Tag:
    """Create the header section with title and explanatory text.

    Returns:
        ui.Tag: A div containing the header content.
    """
    return ui.div(
        {"class": "row mb-4"},
        ui.div(
            {"class": "col-12"},
            ui.h2("Global Support for Ukraine", class_="mb-3"),
            ui.markdown(_get_overview_text()),
        ),
    )


def _get_overview_text() -> str:
    return """The Timeseries page provides interactive visualizations showing how aid to Ukraine has evolved over time since the invasion began in early 2022. It displays multiple perspectives on temporal patterns in aid distribution, from overall support trends to specific breakdowns by type and donor.

Individual Cards:
- Aid Allocation Card: Shows the progress of aid delivery compared to commitments across different country groups (US, EU, and other donors) to show the overall scope of aid.
- Total Support Card: Tracks the cumulative value of total support over time, comparing contributions from the United States, Europe and other donors, allowing users to see how overall aid has accumulated.
- Aid Types Card: Breaks down monthly aid flows by category (military, financial, humanitarian), with the option to view either monthly amounts or cumulative totals, showing how different types of support have evolved.
"""


class TimeSeriesPageServer:
    """Server logic coordinator for the time series page components.

    This class manages the initialization and coordination of all server-side
    components on the time series page, including multiple visualization cards
    showing different aspects of temporal aid patterns.

    Attributes:
        input (ModuleInput): Shiny input object containing user interface values.
        output (ModuleOutput): Shiny output object for rendering visualizations.
        session (Session): Shiny session object.
        total_support (TotalSupportServer): Server instance for total support visualization.
        aid_types (AidTypesServer): Server instance for aid types visualization.
        aid_allocation (AidAllocationServer): Server instance for aid allocation visualization.
    """

    def __init__(
        self,
        input: Any,
        output: Any,
        session: Session,
    ) -> None:
        """Initialize the time series page server coordinator.

        Args:
            input: Shiny input object.
            output: Shiny output object.
            session: Shiny session object.
        """
        self.input = input
        self.output = output
        self.session = session

        # Initialize visualization components
        self.total_support = TotalSupportServer(input, output, session)
        self.aid_types = AidTypesServer(input, output, session)
        self.aid_allocation = AidAllocationServer(input, output, session)

        # Initialize all components
        self.initialize()

    def initialize(self) -> None:
        """Initialize all server-side components.

        This method ensures all child components are properly initialized
        and their outputs are registered with Shiny.
        """
        self.total_support.register_outputs()
        self.aid_types.register_outputs()
        self.aid_allocation.register_outputs()
