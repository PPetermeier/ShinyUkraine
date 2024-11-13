from shiny import ui
from .cards.heavy_weapons import HeavyWeaponsCard, HeavyWeaponsServer
from .cards.weapons_stocks import WeaponsStocksCard, WeaponsStocksServer  # Add import
from .cards.pledge_stock_ratio import PledgeStockCard, PledgeStockServer
from .cards.pledges_weapon_types import PlegesWeaponTypesCard, PledgesWeaponTypesServer

def heavy_weapons_page_ui():
    """Return the UI elements for the heavy weapons page."""
    return ui.page_fillable(
        ui.row(
            ui.column(12, WeaponsStocksCard.ui())  # Add stocks card first
        ),
        ui.row(ui.column(12, HeavyWeaponsCard.ui())),
        ui.row(ui.column(12, PledgeStockCard.ui())),
        ui.row(ui.column(12, PlegesWeaponTypesCard.ui())),
    )


class HeavyWeaponsPageServer:
    """Coordinates all cards on the heavy weapons page."""

    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session

        # Initialize card servers
        self.weapons_stocks = WeaponsStocksServer(input, output, session)  # Add new server
        self.heavy_weapons = HeavyWeaponsServer(input, output, session)
        self.pledge_stock_ratio = PledgeStockServer(input, output, session)
        self.pledges_weapon_types = PledgesWeaponTypesServer(input, output, session)

        # Important: Initialize right away
        self.initialize()

    def initialize(self):
        """Initialize all card servers."""
        self.weapons_stocks.register_outputs()  # Register new outputs
        self.heavy_weapons.register_outputs()
        self.pledge_stock_ratio.register_outputs()
        self.pledges_weapon_types.register_outputs()
