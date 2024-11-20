"""
Map visualization card for displaying country-level support data.
"""

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE, LAST_UPDATE, MARGIN
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
                    "Toggle between total support values and percentage of GDP.",
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
                    ui.input_radio_buttons(
                        "map_display_mode",
                        "Display Mode",
                        choices={
                            "gdp": "As % of GDP",
                            "total": "Total Value (Billion €)",
                        },
                        selected="gdp",
                    ),
                    position="fixed",
                    min_width="300px",
                    max_width="300px",
                    bg="#f8f8f8",
                ),
                output_widget("map_plot", height="700px"),  # Fixed height
            ),
            class_="h-full",
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
            base_color = COLOR_PALETTE.get(aid_type)
        else:
            base_color = COLOR_PALETTE.get("Total Bilateral")

        return [[0, "rgba(255,255,255,1)"], [1, base_color]]

    def _compute_filtered_data(self):
        """Compute filtered data based on selected aid types."""
        selected_types = self.input.map_aid_types()
        if not selected_types:
            return pd.DataFrame()
        query = build_map_support_query(selected_types)

        data = load_data_from_table(
            table_name_or_query=query,
            columns=None,
            where_clause=None,
            order_by=None,
        )
        return data

    def create_map(self):
        """Create and return the choropleth map figure."""
        data = self._filtered_data()
        if data.empty:
            return go.Figure()

        display_mode = self.input.map_display_mode()
        colorscale = self._get_color_scale(self.input.map_aid_types())

        # Choose which value to display based on display mode
        if display_mode == "gdp":
            z_values = data["pct_gdp"]
            colorbar_title = "% of GDP"
            hover_template = (
                "%{text}<br>"
                "Total displayed Support: %{customdata[0]:.1f}B €<br>"
                "% of GDP: %{z:.2f}%"
                "<extra></extra>"
            )
        else:
            z_values = data["total_support"]
            colorbar_title = "Billion €"
            hover_template = (
                "%{text}<br>"
                "Total displayed Support: %{z:.1f}B €<br>"
                "% of GDP: %{customdata[1]:.2f}%"  # Changed from customdata[0] to customdata[1]
                "<extra></extra>"
            )

        fig = go.Figure(
            data=go.Choropleth(
                locations=data["iso3_code"],
                z=z_values,
                text=data["country"],
                customdata=data[["total_support", "pct_gdp"]].values,  # Order matters here
                hovertemplate=hover_template,
                colorscale=colorscale,
                autocolorscale=False,
                zmin=0,
                zmax=z_values.max(),
                marker_line_color="white",
                marker_line_width=0.5,
                colorbar_title=colorbar_title,
            )
        )
        fig.add_choropleth(
            locations=["UKR"],
            z=[1],  # Dummy value, won't be visible
            text=["Ukraine"],
            hovertemplate="Ukraine<extra></extra>",
            colorscale=[[0, COLOR_PALETTE.get("Ukraine Map")], [1, COLOR_PALETTE.get("Ukraine Map")]],
            showscale=False,
            marker_line_color="white",
            marker_line_width=0.5,
        )

        title = "Bilateral Support " + ("as Percentage of GDP" if display_mode == "gdp" else "in Billion €")
        fig.update_layout(
            title=dict(text=f"{title}<br><sub>Last updated: {LAST_UPDATE}, Sheet: Country Summary(€)</sub>", font=dict(size=14), y=0.95, x=0.5, xanchor="center", yanchor="top"),
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
                lataxis_range=[-60, 90],
                lonaxis_range=[-180, 180],
                projection_scale=1.1,
            ),
            autosize=True,
            height=700,  # Fixed pixel height
            margin=dict(l=0, r=0, t=50, b=0, pad=0),
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
