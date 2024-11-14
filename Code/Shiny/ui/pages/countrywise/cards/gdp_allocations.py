"""
GDP-relative allocations visualization card with dynamic height scaling.
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
            # Remove fixed height from card
        )



class GDPAllocationsServer:
    """Server logic for the GDP allocations visualization card."""

    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
        
        # Load and join the data from both tables
        df_allocations = load_data_from_table("f_bilateral_allocations_gdp_pct")
        df_summary = load_data_from_table("a_summary_€")
        
        # Merge the dataframes
        self.df = pd.merge(
            df_allocations,
            df_summary[["country", "share_in_total_eu_allocations__2021_gdp"]],
            on="country",
            how="left"
        )
        
        self._filtered_data = reactive.Calc(self._compute_filtered_data)
        self.register_outputs()

    def _compute_filtered_data(self):
        """Filter and process data based on user selections."""
        # Filter data
        result = self.df.copy()
        allocation_cols = [
            "total_bilateral_allocations",
            "refugee_cost_estimation",
            "share_in_total_eu_allocations__2021_gdp"
        ]

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

        dynamic_height = max(400, len(data) * 40)
        fig = go.Figure()

        # Create lists for each allocation type
        countries = data["country"].tolist()
        bilateral_values = data["total_bilateral_allocations"].tolist()
        refugee_values = data["refugee_cost_estimation"].tolist()
        eu_share_values = data["share_in_total_eu_allocations__2021_gdp"].tolist()

        # Add bilateral allocations trace
        fig.add_trace(
            go.Bar(
                y=countries,
                x=bilateral_values,
                name="Total bilateral allocations",
                orientation="h",
                marker_color=COLOR_PALETTE.get("total_bilateral",),
                hovertemplate="%{y}<br>Value: %{x:.2f}% of GDP<extra></extra>",
            )
        )

        # Add refugee costs trace
        fig.add_trace(
            go.Bar(
                y=countries,
                x=refugee_values,
                name="Refugee cost estimation",
                orientation="h",
                marker_color=COLOR_PALETTE.get("refugee"),
                hovertemplate="%{y}<br>Value: %{x:.2f}% of GDP<extra></extra>",
            )
        )

        # Add EU share trace
        fig.add_trace(
            go.Bar(
                y=countries,
                x=eu_share_values,
                name="Share in total EU allocations",
                orientation="h",
                marker_color=COLOR_PALETTE.get("europe"), 
                hovertemplate="%{y}<br>Value: %{x:.2f}% of GDP<extra></extra>",
            )
        )

        title = "Bilateral Aid, Refugee Costs, and EU Share"
        fig.update_layout(
            title=dict(
                text=f"{title}<br><sub>Last updated: {LAST_UPDATE}</sub>",
                font=dict(size=14),
                y=0.95,
                x=0.5,
                xanchor="center",
                yanchor="top",
            ),
            xaxis_title="Percentage of 2021 GDP",
            barmode="stack",
            template="plotly_white",
            height=dynamic_height,
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
                tickfont=dict(size=12),
                categoryorder="total ascending",
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