"""
GDP-relative allocations visualization card.
"""

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE, LAST_UPDATE, MARGIN
from server import load_data_from_table
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget


class GDPAllocationsCard:
    """UI components for the GDP allocations visualization card."""

    @staticmethod
    def ui():
        """Return the card UI elements."""
        return ui.card(
            ui.card_header(
                ui.h3("Support to Ukraine and Refugee Costs as Share of GDP"),
                ui.div(
                    {"class": "d-flex justify-content-between"},
                    ui.div(
                        {"class": "card-subtitle text-muted"},
                        "Includes bilateral allocations to Ukraine and cost estimates for refugees in donor countries. "
                        "Allocations are defined as aid which has been delivered or specified for delivery. Does not include "
                        "private donations, support for refugees outside of Ukraine, and aid by international organizations.",
                    ),
                    ui.div(
                        {"class": "d-flex align-items-center"},
                        "First  ",
                        ui.input_numeric(
                            "top_n_countries_gdp_ratio",
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
            output_widget("gdp_allocations_plot"),
            height="800px",
        )


class GDPAllocationsServer:
    """Server logic for the GDP allocations visualization card."""

    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
        self.df = load_data_from_table("f_bilateral_allocations_gdp_pct")
        self._filtered_data = reactive.Calc(self._compute_filtered_data)
        self.register_outputs()

    def _compute_filtered_data(self):
        """Filter and process data based on user selections."""
        # Filter data
        result = self.df.copy()
        allocation_cols = ["total_bilateral_allocations", "refugee_cost_estimation"]

        # Calculate total for sorting
        result["total"] = result[allocation_cols].sum(axis=1)

        # Get top N countries and sort
        result = result.nlargest(self.input.top_n_countries_gdp_ratio(), "total")
        result = result.sort_values("total", ascending=True)

        # Return needed columns
        return result[["country"] + allocation_cols]

    def create_plot(self):
        """Create and return the plot figure."""
        data = self._filtered_data()

        if data.empty:
            return go.Figure()

        fig = go.Figure()

        # Color mapping
        colors = {
            "total_bilateral_allocations": COLOR_PALETTE.get("base_color", "#1f77b4"),
            "refugee_cost_estimation": COLOR_PALETTE.get("refugee", "#ff7f0e"),
        }

        # Name mapping
        name_map = {
            "total_bilateral_allocations": "Total bilateral allocations",
            "refugee_cost_estimation": "Refugee cost estimation",
        }

        # Add bars for each allocation type
        for alloc_type, color in colors.items():
            fig.add_trace(
                go.Bar(
                    y=data["country"],
                    x=data[alloc_type],
                    name=name_map[alloc_type],
                    orientation="h",
                    marker_color=color,
                    hovertemplate="%{y}<br>" + "%{customdata}<br>" + "Value: %{x:.2f}% of GDP<extra></extra>",
                    customdata=[name_map[alloc_type]] * len(data),
                )
            )

        title = "Bilateral Aid and Refugee cost estimation"
        fig.update_layout(
            title=dict(text=f"{title}<br><sub>Last updated: {LAST_UPDATE}</sub>", font=dict(size=14), y=0.95, x=0.5, xanchor="center", yanchor="top"),
            xaxis_title="Percentage of 2021 GDP",
            barmode="stack",
            template="plotly_white",
            height=600,
            margin=MARGIN,
            legend=dict(yanchor="bottom", y=0.01, xanchor="right", x=0.99, bgcolor="rgba(255, 255, 255, 0.8)", bordercolor="rgba(0, 0, 0, 0.2)", borderwidth=1),
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
                tickformat=".1f",
            ),
            plot_bgcolor="rgba(255,255,255,1)",
            paper_bgcolor="rgba(255,255,255,1)",
        )
        return fig

    def register_outputs(self):
        """Register all outputs for the module."""

        @self.output
        @render_widget
        def gdp_allocations_plot():
            return self.create_plot()
