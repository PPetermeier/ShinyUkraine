"""
Heavy weapons deliveries visualization card.
"""

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE, LAST_UPDATE, MARGIN
from server.database import load_data_from_table
from server.queries import HEAVY_WEAPONS_DELIVERY_QUERY
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget


class HeavyWeaponsCard:
    """UI components for the heavy weapons delivery visualization card."""

    @staticmethod
    def ui():
        """Return the card UI elements."""
        return ui.card(
            ui.card_header(
                ui.div(
                    {"class": "d-flex justify-content-between align-items-center"},
                    ui.div(
                        {"class": "flex-grow-1"},
                        ui.h3("Heavy Weapons Deliveries"),
                        ui.div(
                            {"class": "card-subtitle text-muted"},
                            "This figure shows the delivery of heavy weapons to Ukraine by country over time (in number of units).",
                        ),
                    ),
                    ui.div(
                        {"class": "ms-3 d-flex align-items-center"},
                        ui.span({"class": "me-2"}, "Top"),
                        ui.input_numeric(
                            "top_n_countries_heavy_weapons",
                            None,  # No label needed as it's inline
                            value=10,
                            min=5,
                            max=20,
                            width="80px",
                        ),
                        ui.span({"class": "ms-2"}, "countries",),
                    ),
                ),
            ),
            output_widget("heavy_weapons_plot"),
            height="800px",
        )



class HeavyWeaponsServer:
    """Server logic for the heavy weapons delivery visualization card."""

    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
        self._filtered_data = reactive.Calc(self._compute_filtered_data)

    def _compute_filtered_data(self):
        """Internal method to compute filtered data based on user inputs."""
        # Load data using the predefined query
        df = load_data_from_table(table_name_or_query=HEAVY_WEAPONS_DELIVERY_QUERY)

        # Sort by total deliveries and get top N countries
        df = df.nlargest(self.input.top_n_countries(), "value_estimates_heavy_weapons")
        df = df.sort_values("value_estimates_heavy_weapons", ascending=True)  # For bottom-to-top display

        return df

    def create_plot(self):
        """Create and return the plot figure."""
        data = self._filtered_data()

        if data.empty:
            return go.Figure()

        fig = go.Figure()

        # Add horizontal bars for heavy weapons value estimates
        fig.add_trace(
            go.Bar(
                x=data["value_estimates_heavy_weapons"],
                y=data["country"],
                orientation="h",
                marker_color=COLOR_PALETTE.get("heavy_weapons_deliveries", "#E76F51"),
                hovertemplate="%{y}<br>" + "Value Estimate: %{x:.1f}B €<extra></extra>",
            )
        )

        title = "Estimated Value of Heavy Weapons Delivered to Ukraine"
        fig.update_layout(
            title=dict(
                text=f"{title}<br><sub>Last updated: {LAST_UPDATE}</sub>",
                font=dict(size=14),
                y=0.95,
                x=0.5,
                xanchor='center',
                yanchor='top'
            ),
            xaxis_title="Estimated Value Billion €",
            yaxis_title="",
            barmode="stack",
            template="plotly_white",
            height=600,
            margin=MARGIN,
            legend=dict(yanchor="bottom", y=0.01, xanchor="right", x=0.99, bgcolor="rgba(255, 255, 255, 0.8)", bordercolor="rgba(0, 0, 0, 0.2)", borderwidth=1),
            showlegend=False,
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
        def heavy_weapons_plot():
            return self.create_plot()
