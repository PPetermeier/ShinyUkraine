"""
Country and aid type visualization card.
"""

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE, LAST_UPDATE, MARGIN
from server import load_country_data
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget


class CountryAidCard:
    """UI components for the country aid visualization card."""

    @staticmethod
    def ui():
        """Return the card UI elements."""
        return ui.card(
            ui.card_header(
                ui.h3("Bilateral aid by country and type"),
                ui.div(
                    {"class": "d-flex justify-content-between"},
                    ui.div(
                        {"class": "card-subtitle text-muted"},
                        "Includes bilateral allocations to Ukraine and cost estimates for refugees in donor countries. "
                        "Allocations are defined as aid which has been delivered or specified for delivery. Does not include "
                        "private donations, support for refugees outside of Ukraine, and aid by international organizations. "
                        "Data on European Union aid include the EU Commission and Council, EPF, and EIB. For information on "
                        "data quality and transparency please see our data transparency index.",
                    ),
                    ui.div(
                        {"class": "d-flex align-items-center"},
                        "First  ",
                        ui.input_numeric(
                            "top_n_countries_total_aid",
                            None,
                            value=15,
                            min=5,
                            max=50,
                            width="80px",
                        ),
                        " countries",
                    ),
                ),
            ),
            output_widget("country_aid_plot"),
            height="800px",
        )


class CountryAidServer:
    """Server logic for the country aid visualization card."""

    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
        self.df = load_country_data()
        self._filtered_data = reactive.Calc(self._compute_filtered_data)
        self.register_outputs()

    def _compute_filtered_data(self):
        """Filter and process data based on user selections."""
        # Get all aid type columns
        aid_cols = ["financial", "humanitarian", "military", "refugee_cost_estimation"]

        # Filter data
        result = self.df.copy()

        # Calculate total aid for sorting
        result["total_aid"] = result[aid_cols].sum(axis=1)

        # Get top N countries and sort
        result = result.nlargest(self.input.top_n_countries_total_aid(), "total_aid")
        result = result.sort_values("total_aid", ascending=True)

        # Return all columns needed for plotting
        return result[["country"] + aid_cols]

    def create_plot(self):
        """Create and return the plot figure."""
        data = self._filtered_data()

        if data.empty:
            return go.Figure()

        fig = go.Figure()

        # Color mapping for aid types
        colors = {
            "financial": COLOR_PALETTE.get("financial"),
            "humanitarian": COLOR_PALETTE.get("humanitarian"),
            "military": COLOR_PALETTE.get("military"),
            "refugee_cost_estimation": COLOR_PALETTE.get("refugee"),
        }

        # Name mapping for aid types
        name_map = {"financial": "Financial", "humanitarian": "Humanitarian", "military": "Military", "refugee_cost_estimation": "Refugee Support"}

        # Add bars for each aid type
        for aid_type, color in colors.items():
            fig.add_trace(
                go.Bar(
                    y=data["country"],
                    x=data[aid_type],
                    name=name_map[aid_type],
                    orientation="h",
                    marker_color=color,
                )
            )


        title = "Aid Allocation by Country and Type"
        fig.update_layout(
            title=dict(
                text=f"{title}<br><sub>Last updated: {LAST_UPDATE}</sub>",
                font=dict(size=14),
                y=0.95,
                x=0.5,
                xanchor="center",
                yanchor="top",
            ),
            xaxis_title="Billion €",
            barmode="stack",
            template="plotly_white",
            height=600,
            margin=MARGIN,
            legend=dict(
                yanchor="bottom",
                y=0.01,
                xanchor="right",
                x=0.99,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.2)",
                borderwidth=1,
            ),
            showlegend=True,
            hovermode="y unified",
            autosize=True,
            yaxis=dict(
                showgrid=False,
                gridcolor="rgba(0,0,0,0.1)",
                zerolinecolor="rgba(0,0,0,0.2)",
            ),
            xaxis=dict(
                showgrid=False,
                gridcolor="rgba(0,0,0,0.1)",
                zerolinecolor="rgba(0,0,0,0.2)",
            ),
            plot_bgcolor="rgba(255,255,255,1)",
            paper_bgcolor="rgba(255,255,255,1)",
        )
        return fig

    def register_outputs(self):
        """Register all outputs for the module."""

        @self.output
        @render_widget
        def country_aid_plot():
            return self.create_plot()
