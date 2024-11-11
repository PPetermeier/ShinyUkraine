# app.py

from shiny import App
from ui import get_main_ui
from ui.pages.countrywise import CountryAidPageServer
from ui.pages.landing import LandingPageServer
from ui.pages.timeseries import TimeSeriesPageServer
from ui.pages.financial import FinancialPageServer
from ui.pages.weapons import HeavyWeaponsPageServer  # Import the new page server

def server(input, output, session):
    # Initialize the landing page server
    landing_server = LandingPageServer(input, output, session)
    landing_server.initialize()

    # Initialize the time series page server
    ts_server = TimeSeriesPageServer(input, output, session)
    ts_server.initialize()

    # Initialize the country aid page server
    ca_server = CountryAidPageServer(input, output, session)
    ca_server.initialize()

    # Initialize the financial aid page server
    financial_server = FinancialPageServer(input, output, session)
    financial_server.initialize()

    # Initialize the weapons page server
    weapons_server = HeavyWeaponsPageServer(input, output, session)
    weapons_server.initialize()  # Don't forget to initialize the new server

app = App(get_main_ui(), server)