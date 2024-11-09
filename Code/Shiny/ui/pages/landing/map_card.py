"""
Map visualization card for displaying country-level support data.
"""

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE
from server.database import load_data_from_table
from server.queries import MAP_SUPPORT_TYPES, build_map_support_query
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget


class MapCard:
    """UI components for the map visualization card."""

    @staticmethod
    def ui():
        return ui.card(
            ui.card_header(
                ui.h3("Total Bilateral Support by Country"),
                ui.div(
                    {"class": "card-subtitle text-muted"},
                    "Bilateral aid allocations to Ukraine as percentage of donor country's 2021 GDP.",
                ),
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
                    position="fixed",
                    min_width="300px",
                    max_width="300px",
                    bg="#f8f8f8",
                ),
                output_widget("map_plot"),
            ),
            height="800px",
        )


class MapServer:
    """Server logic for the map visualization card."""

    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
        self._filtered_data = reactive.Calc(self._compute_filtered_data)

    def _get_color_scale(self, selected_types):
        """Get color scale based on selected aid types."""
        if len(selected_types) == 1:
            # Fix for refugee_cost_estimation mapping to refugee in COLOR_PALETTE
            aid_type = "refugee" if selected_types[0] == "refugee_cost_estimation" else selected_types[0]
            base_color = COLOR_PALETTE.get(aid_type, "#003399")
        else:
            base_color = "#003399"

        return [[0, "rgba(255,255,255,1)"], [1, base_color]]

    def _compute_filtered_data(self):
        """Compute filtered data based on selected aid types."""
        selected_types = self.input.map_aid_types()
        if not selected_types:
            return pd.DataFrame()
        query = build_map_support_query(selected_types)

        # Making it explicit that we're executing a complex query
        data = load_data_from_table(
            table_name_or_query=query,  # Using the named parameter
            columns=None,  # Not needed for complex query
            where_clause=None,  # Not needed for complex query
            order_by=None,  # Not needed for complex query
        )
        return data

    def create_map(self):
        """Create and return the choropleth map figure."""
        data = self._filtered_data()
        if data.empty:
            return go.Figure()

        colorscale = self._get_color_scale(self.input.map_aid_types())

        fig = go.Figure(
            data=go.Choropleth(
                locations=data["iso3_code"],
                z=data["pct_gdp"],
                text=data.apply(
                    lambda row: (f"{row['country']}<br>" f"Total Support: {row['total_support']:.1f}B €<br>" f"% of GDP: {row['pct_gdp']:.2f}%"), axis=1
                ),
                hovertemplate="%{text}<extra></extra>",
                colorscale=colorscale,
                autocolorscale=False,
                zmin=0,
                zmax=data["pct_gdp"].max(),
                marker_line_color="white",
                marker_line_width=0.5,
                colorbar_title="% of GDP",
            )
        )

        fig.update_layout(
            title_text="Bilateral Support as Percentage of GDP",
            geo=dict(
                showframe=False,
                showcoastlines=True,
                projection_type="equirectangular",
                coastlinecolor="rgba(0,0,0,0.2)",
                countrycolor="rgba(0,0,0,0.2)",
                showland=True,
                landcolor="rgba(240,240,240,1)",
                showocean=True,
                oceancolor="rgba(250,250,250,1)",
                # Add these parameters to adjust the map view
                lataxis_range=[-60, 90],  # Exclude Antarctica
                lonaxis_range=[-180, 180],
                projection_scale=1.1,  # Make the map a bit wider
            ),
            width=None,
            height=600,
            autosize=True,
            margin={"r": 0, "t": 30, "l": 0, "b": 0},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    def register_outputs(self):
        """Register all outputs for the module."""

        @self.output
        @render_widget
        def map_plot():
            return self.create_map()
