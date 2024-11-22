"""Landing page module for the Ukraine Support Tracker visualization.

This module defines the main landing page layout and server coordination for the
Ukraine Support Tracker application. It includes the page structure, explanatory text,
and coordinates the various visualization components, particularly the main map display.

The landing page provides an overview of global support for Ukraine across different
aid categories (military, financial, humanitarian, and refugee support) since
Russia's invasion in February 2022.
"""

from typing import Any
from shiny import Session, ui

from .map_card import MapCard, MapCardServer


def map_page_ui() -> ui.page_fillable:
    """Create the user interface elements for the landing page.

    Returns:
        ui.Page: A Shiny page containing the main layout and map visualization.
    """
    return ui.page_fillable(
        ui.div(
            {"class": "container-fluid"},
            _create_header_section(),
            _create_map_section(),
        )
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


def _create_map_section() -> ui.Tag:
    """Create the section containing the map visualization.

    Returns:
        ui.Tag: A div containing the map card.
    """
    return ui.div(
        {"class": "row"},
        ui.div({"class": "col-12"}, MapCard.ui()),
    )


def _get_overview_text() -> str:
    """Get the markdown text explaining the tracker's purpose and data coverage.

    Returns:
        str: Formatted markdown text describing the visualization.
    """
    return """
The map displays a global visualization of support for Ukraine from donor countries since Russia's invasion in 2022. It allows you to explore different types of aid that countries have provided to Ukraine, including military support, financial aid, humanitarian assistance, and refugee-related costs.
The visualization offers two main views:

Total value in billion Euros: Shows the absolute amount of aid provided by each country
As percentage of GDP: Shows the relative generosity of donors by scaling aid to their economic size

Countries that have provided more support are shown in darker shades of blue, while those providing less support appear in lighter shades. The map is interactive - you can hover over countries to see the exact values of their contributions.
You can customize the view using the sidebar controls to:

Select which types of support to include in the visualization
Switch between absolute values and GDP-relative views
See how different types of aid are distributed globally

This helps provide a clear geographic picture of which countries are contributing most substantially to supporting Ukraine, both in absolute terms and relative to their economic capacity.
        """


class MapPageServer:
    """Server logic coordinator for the landing page components.

    This class manages the initialization and coordination of all server-side
    components on the landing page, particularly the map visualization.

    Attributes:
        input (ModuleInput): Shiny input object containing user interface values.
        output (ModuleOutput): Shiny output object for rendering visualizations.
        session (Session): Shiny session object.
        map_card (MapServer): Server instance for the map visualization.
    """

    def __init__(
        self,
        input: Any,
        output: Any,
        session: Session,
    ) -> None:
        """Initialize the landing page server coordinator.

        Args:
            input: Shiny input object.
            output: Shiny output object.
            session: Shiny session object.
        """
        self.input = input
        self.output = output
        self.session = session

        # Initialize visualization components
        self.map_card = MapCardServer(input, output, session)

        # Initialize all components
        self.initialize()

    def initialize(self) -> None:
        """Initialize all server-side components.

        This method ensures all child components are properly initialized
        and their outputs are registered with Shiny.
        """
        self.map_card.register_outputs()
