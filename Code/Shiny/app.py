from shiny import App
from ui import get_main_ui
from ui.pages.timeseries import TimeSeriesPageServer
from ui.pages.countrywise import CountryAidPageServer

def server(input, output, session):
    # Initialize the time series page server
    ts_server = TimeSeriesPageServer(input, output, session)
    ts_server.initialize()
    
    # Initialize the country aid page server
    ca_server = CountryAidPageServer(input, output, session)
    ca_server.initialize()

app = App(get_main_ui(), server)
