"""Module for managing the weapons support visualization page.

This module coordinates the display and interaction of multiple visualization cards
related to weapons support for Ukraine. It provides comprehensive views of:
- Weapons stocks comparisons across countries
- Heavy weapons deliveries and their status
- Pledge-to-stock ratios showing commitment levels
- Weapon type-specific pledges and distributions

The module maintains a clear separation between layout management and server-side
coordination while providing a consistent interface for all visualization components.
"""

from typing import Any

from shiny import Session, ui

from .cards.a_weapons_stocks import WeaponsStocksCard, WeaponsStocksServer
from .cards.b_heavy_weapons import HeavyWeaponsCard, HeavyWeaponsServer
from .cards.c_pledge_stock_ratio import PledgeStockCard, PledgeStockServer
from .cards.d_pledges_weapon_types import WeaponTypesCard, WeaponTypesServer


class WeaponsPageLayout:
    """Manages the layout and structure of the weapons page.

    This class defines the organization and presentation of visualization cards
    on the weapons support page, maintaining a consistent ordering and layout
    structure for all components.

    Class Attributes:
        CARD_COMPONENTS: Ordered list of card component classes to be displayed
            on the page.
    """

    CARD_COMPONENTS: list[type[ui.Tag]] = [
        WeaponsStocksCard,
        HeavyWeaponsCard,
        PledgeStockCard,
        WeaponTypesCard,
    ]

    @staticmethod
    def create_ui() -> ui.page_fillable:
        """Create the user interface for the weapons page.

        Returns:
            ui.Page: A Shiny page containing all weapon-related visualization
                cards arranged in a vertical layout with consistent spacing.
        """
        return ui.page_fillable(
            ui.div(
                {"class": "container-fluid"},
                ui.div(
                    {"class": "row g-4"},  # Add consistent spacing between cards
                    *[
                        _create_card_section(card)
                        for card in WeaponsPageLayout.CARD_COMPONENTS
                    ],
                ),
            )
        )


def _create_card_section(card_component: type[ui.Tag]) -> ui.Tag:
    """Create a section for a single visualization card.

    Args:
        card_component: The card component class to create a section for.

    Returns:
        ui.Tag: A column containing the specified card component.
    """
    return ui.div({"class": "col-12"}, card_component.ui())


class WeaponsPageServer:
    """Coordinates all visualization cards on the weapons page.

    This class manages the server-side components for all weapon-related
    visualizations, handling their initialization and coordination while
    maintaining consistent state management across components.

    Attributes:
        input (ModuleInput): Shiny input object containing user interface values.
        output (ModuleOutput): Shiny output object for rendering visualizations.
        session (Session): Shiny session object.
        servers (Dict[str, Any]): Dictionary of initialized card servers.
    """

    def __init__(
        self,
        input: Any,
        output: Any,
        session: Session,
    ) -> None:
        """Initialize the page server and all card servers.

        Args:
            input: Shiny input object.
            output: Shiny output object.
            session: Shiny session object.
        """
        self.input = input
        self.output = output
        self.session = session

        # Initialize all card servers with consistent naming
        self.servers: dict[str, Any] = {
            "weapons_stocks": WeaponsStocksServer(input, output, session),
            "heavy_weapons": HeavyWeaponsServer(input, output, session),
            "pledge_stock": PledgeStockServer(input, output, session),
            "weapon_types": WeaponTypesServer(input, output, session),
        }

        self.initialize()

    def initialize(self) -> None:
        """Initialize and register outputs for all card servers.

        This method ensures all visualization components are properly initialized
        and their outputs are registered with the Shiny server.
        """
        for server in self.servers.values():
            server.register_outputs()


def weapons_page_ui() -> ui.page_fillable:
    """Create the UI elements for the weapons page.

    Returns:
        ui.Page: A Shiny page containing all weapon-related visualizations
            arranged in a consistent and visually appealing layout.
    """
    return WeaponsPageLayout.create_ui()
