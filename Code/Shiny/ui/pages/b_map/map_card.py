"""Module for visualizing geographical distribution of support to Ukraine.

This module provides components for creating and managing an interactive choropleth map
visualization that shows bilateral support either as total values or as percentage of GDP,
with configurable support types and display modes.
"""

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE, LAST_UPDATE
from server.database import load_data_from_table
from server.queries import MAP_SUPPORT_TYPES, build_map_support_query
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget


class MapCard:
    """UI components for the map visualization card.

    This class handles the user interface elements for displaying and controlling
    the geographical visualization of support data.
    """

    DISPLAY_MODES: dict[str, str] = {
        "gdp": "As % of GDP",
        "total": "Total Value (Billion €)",
    }

    @staticmethod
    def ui() -> ui.card:
        """Create the user interface elements for the visualization card.

        Returns:
            ui.card: A Shiny card containing the map visualization and control elements.
        """
        return ui.card(
            ui.card_header(
                ui.h3("Total Bilateral Support by Donor Country and Category"),
            ),
            ui.layout_sidebar(
                ui.sidebar(
                    "Input options",
                    ui.input_checkbox_group(
                        "map_aid_types",
                        "Select Support Types",
                        choices=MAP_SUPPORT_TYPES,
                        selected=list(MAP_SUPPORT_TYPES.keys()),
                    ),
                    ui.input_radio_buttons(
                        "map_display_mode",
                        "Display Mode",
                        choices=MapCard.DISPLAY_MODES,
                        selected="gdp",
                    ),
                    position="fixed",
                    min_width="300px",
                    max_width="300px",
                    bg="#f8f8f8",
                ),
                output_widget("map_plot", height="700px"),
            ),
            class_="h-full",
        )


class MapCardServer:
    """Server logic for the map visualization.

    This class handles data processing, filtering, and map generation for the
    geographical visualization of support data.

    Attributes:
        input: Shiny input object containing user interface values.
        output: Shiny output object for rendering visualizations.
        session: Shiny session object.
    """

    # Define display mode configurations
    DISPLAY_CONFIGS: dict[str, dict[str, str]] = {
        "gdp": {
            "value_column": "pct_gdp",
            "colorbar_title": "% of GDP",
            "hover_template": "%{text}<br>Total displayed Support: %{customdata[0]:.1f}B €<br>% of GDP: %{z:.2f}%",
            "title_suffix": "as Percentage of GDP",
        },
        "total": {
            "value_column": "total_support",
            "colorbar_title": "Billion €",
            "hover_template": "%{text}<br>Total displayed Support: %{z:.1f}B €<br>% of GDP: %{customdata[1]:.2f}%",
            "title_suffix": "in Billion €",
        },
    }

    # Define map style configurations
    MAP_STYLE: dict = {
        "geo": {
            "showframe": False,
            "showcoastlines": True,
            "projection_type": "equirectangular",
            "coastlinecolor": "rgba(0,0,0,0.2)",
            "countrycolor": "rgba(0,0,0,0.2)",
            "showland": True,
            "landcolor": "rgba(240,240,240,1)",
            "showocean": True,
            "oceancolor": "rgba(250,250,250,1)",
            "lataxis_range": [-60, 90],
            "lonaxis_range": [-180, 180],
            "projection_scale": 1.1,
        },
        "layout": {
            "autosize": True,
            "height": 700,
            "margin": dict(l=0, r=0, t=50, b=0, pad=0),
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
        },
    }

    def __init__(self, input, output, session):
        """Initialize the server component.

        Args:
            input: Shiny input object.
            output: Shiny output object.
            session: Shiny session object.
        """
        self.input = input
        self.output = output
        self.session = session
        self._filtered_data = reactive.Calc(self._compute_filtered_data)

    def _get_color_scale(self, selected_types: list[str]) -> list[list]:
        """Get color scale based on selected aid types.

        Args:
            selected_types: List of selected aid type identifiers.

        Returns:
            List of color scale specifications for the choropleth map.
        """
        if len(selected_types) == 1:
            # Fix for refugee_cost_estimation mapping to refugee in COLOR_PALETTE
            aid_type = (
                "refugee"
                if selected_types[0] == "refugee_cost_estimation"
                else selected_types[0]
            )
            base_color = COLOR_PALETTE.get(aid_type)
        else:
            base_color = COLOR_PALETTE.get("Total Bilateral")

        return [[0, "rgba(255,255,255,1)"], [1, base_color]]

    def _compute_filtered_data(self) -> pd.DataFrame:
        """Compute filtered data based on selected aid types.

        Returns:
            pd.DataFrame: Filtered DataFrame containing support data.
        """
        selected_types = self.input.map_aid_types()
        if not selected_types:
            return pd.DataFrame()

        query = build_map_support_query(selected_types)
        return load_data_from_table(query)

    def create_map(self) -> go.Figure:
        """Generate the choropleth map visualization.

        Returns:
            go.Figure: Plotly figure object containing the choropleth map.
        """
        data = self._filtered_data()
        if data.empty:
            return go.Figure()

        fig = self._create_choropleth_map(data)
        self._add_ukraine_overlay(fig)
        self._update_map_layout(fig)

        return fig

    def _create_choropleth_map(self, data: pd.DataFrame) -> go.Figure:
        """Create the main choropleth map visualization.

        Args:
            data: DataFrame containing support data.

        Returns:
            go.Figure: Configured choropleth map figure.
        """
        display_mode = self.input.map_display_mode()
        config = self.DISPLAY_CONFIGS[display_mode]
        colorscale = self._get_color_scale(self.input.map_aid_types())

        fig = go.Figure(
            data=go.Choropleth(
                locations=data["iso3_code"],
                z=data[config["value_column"]],
                text=data["country"],
                customdata=data[["total_support", "pct_gdp"]].values,
                hovertemplate=config["hover_template"],
                colorscale=colorscale,
                autocolorscale=False,
                zmin=0,
                zmax=data[config["value_column"]].max(),
                marker_line_color="white",
                marker_line_width=0.5,
                colorbar_title=config["colorbar_title"],
            )
        )
        return fig

    def _add_ukraine_overlay(self, fig: go.Figure) -> None:
        """Add Ukraine overlay to the map.

        Args:
            fig: Plotly figure object to update.
        """
        fig.add_choropleth(
            locations=["UKR"],
            z=[1],
            text=["Ukraine"],
            hovertemplate="Ukraine<extra></extra>",
            colorscale=[
                [0, COLOR_PALETTE.get("Ukraine Map")],
                [1, COLOR_PALETTE.get("Ukraine Map")],
            ],
            showscale=False,
            marker_line_color="white",
            marker_line_width=0.5,
        )

    def _update_map_layout(self, fig: go.Figure) -> None:
        """Update the layout of the map figure.

        Args:
            fig: Plotly figure object to update.
        """
        display_mode = self.input.map_display_mode()
        config = self.DISPLAY_CONFIGS[display_mode]

        fig.update_layout(
            title=dict(
                text=f"Bilateral Support {config['title_suffix']}<br>"
                f"<sub>Last updated: {LAST_UPDATE}, Sheet: Country Summary(€)</sub>",
                font=dict(size=14),
                y=0.95,
                x=0.5,
                xanchor="center",
                yanchor="top",
            ),
            geo=self.MAP_STYLE["geo"],
            **self.MAP_STYLE["layout"],
        )

    def register_outputs(self) -> None:
        """Register the map output with Shiny."""

        @self.output
        @render_widget
        def map_plot():
            return self.create_map()
