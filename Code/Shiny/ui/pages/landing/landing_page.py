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

from .map_card import MapCard, MapServer


def landing_page_ui() -> ui.page_fillable:
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
        This tracker provides a comprehensive overview of the support provided to Ukraine
        by partner countries since Russia's invasion in February 2022. The data includes
        bilateral commitments of financial, humanitarian, military support and support
        for refugees from government sources.
        
        The visualization below shows the total amount of support by country across
        different aid categories. You can select specific types of support using the
        controls in the sidebar. All values are in billion euros.
        
        **Note:** The data includes:
        - Military: Direct military aid and military-purposed financial aid
        - Financial: Direct financial aid excluding military purposes
        - Humanitarian: Direct humanitarian assistance
        - Refugee: Support for Ukrainian refugees in host countries
        """


class LandingPageServer:
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
        self.map_card = MapServer(input, output, session)
        
        # Initialize all components
        self.initialize()

    def initialize(self) -> None:
        """Initialize all server-side components.
        
        This method ensures all child components are properly initialized
        and their outputs are registered with Shiny.
        """
        self.map_card.register_outputs()