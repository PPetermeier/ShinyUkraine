"""Module for visualizing military aid pledges as a share of national stocks.

This module provides components for creating and managing an interactive visualization
that shows the percentage of national heavy weapon stocks (tanks, howitzers, MLRS)
that countries have pledged and delivered to Ukraine, split between delivered and
to-be-delivered amounts.
"""

from typing import Any

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE, LAST_UPDATE, MARGIN
from server.database import load_data_from_table
from server.queries import WEAPON_STOCK_PLEDGES_QUERY
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget


class PledgeStockCard:
    """UI components for the weapons stock pledges visualization card.

    This class handles the user interface elements for displaying and controlling
    the weapons stock pledges visualization, including country filtering options.
    """

    @staticmethod
    def ui() -> ui.card:
        """Create the user interface elements for the visualization card.

        Returns:
            ui.card: A Shiny card containing the visualization and control elements.
        """
        return ui.card(
            ui.card_header(
                ui.div(
                    {"class": "d-flex justify-content-between align-items-center"},
                    ui.div(
                        {"class": "flex-grow-1"},
                        ui.h3("Military Aid as Share of National Stocks"),
                        ui.div(
                            {"class": "card-subtitle text-muted"},
                            "This figure shows the average share of heavy weapon stocks committed to Ukraine between January 24, 2022 and August 31, 2024, as percent of country stocks. The average is computed across three main categories of heavy weapons, meaning the average commitment to stock shares of (i) tanks, (ii) howitzers (155, 152 mm), and (iii) multiple rocket launchers (MRLS). Data on stocks is taken from IISS Military Balance (2022) estimates. Only weapons that are ready to be used are considered. There is no differentiation between weapon age, quality, or cost.",
                        ),
                    ),
                    ui.div(
                        {"class": "ms-3 d-flex align-items-center"},
                        ui.span({"class": "me-2"}, "Top"),
                        ui.input_numeric(
                            "numeric_pledge_stocks",
                            None,
                            value=19,
                            min=5,
                            max=30,
                            width="80px",
                        ),
                        ui.span({"class": "ms-2"}, "countries"),
                    ),
                ),
            ),
            output_widget("pledges_weapon_types_plot"),
            height="800px",
        )


class PledgeStockServer:
    """Server logic for the weapons stock pledges visualization.

    This class handles data processing, filtering, and plot generation for the
    weapons stock pledges visualization comparing different countries' contributions.

    Attributes:
        input: Shiny input object containing user interface values.
        output: Shiny output object for rendering visualizations.
        session: Shiny session object.
    """

    # Define visualization properties
    PLOT_CONFIG: dict[str, dict] = {
        "traces": {
            "delivered": {
                "name": "Delivered",
                "color": COLOR_PALETTE.get("military"),
                "hover_template": "Delivered: %{x:.1f}%",
            },
            "to_be_delivered": {
                "name": "To Be Delivered",
                "color": COLOR_PALETTE.get("aid_committed"),
                "hover_template": "To Be Delivered: %{x:.1f}%",
            },
        },
        "title": "Share of National Stocks Pledged to Ukraine",
        "base_height": 600,
        "height_per_country": 40,
    }

    def __init__(self, input: Any, output: Any, session: Any):
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

    def _compute_filtered_data(self) -> pd.DataFrame:
        """Compute filtered data based on user inputs.

        Returns:
            pd.DataFrame: Filtered and sorted DataFrame containing top N countries.
        """
        df = load_data_from_table(table_name_or_query=WEAPON_STOCK_PLEDGES_QUERY)

        # Calculate total pledges and filter for top N countries
        df["total_pledged"] = df["delivered"].fillna(0) + df["to_be_delivered"].fillna(
            0
        )
        return df.nlargest(self.input.numeric_pledge_stocks(), "total_pledged")

    def create_plot(self) -> go.Figure:
        """Generate the weapons stock pledges visualization plot.

        Returns:
            go.Figure: Plotly figure object containing the stacked bar chart.
        """
        data = self._filtered_data()
        if data.empty:
            return go.Figure()

        fig = self._create_stacked_bar_chart(data)
        self._update_figure_layout(fig, len(data))
        return fig

    def _create_stacked_bar_chart(self, data: pd.DataFrame) -> go.Figure:
        """Create a stacked bar chart visualization.

        Args:
            data: DataFrame containing filtered weapons stock pledges data.

        Returns:
            go.Figure: Configured Plotly figure object.
        """
        fig = go.Figure()

        for trace_type, config in self.PLOT_CONFIG["traces"].items():
            fig.add_trace(
                self._create_bar_trace(
                    data=data,
                    value_column=trace_type,
                    name=config["name"],
                    color=config["color"],
                    hover_template=config["hover_template"],
                )
            )

        return fig

    def _create_bar_trace(
        self,
        data: pd.DataFrame,
        value_column: str,
        name: str,
        color: str,
        hover_template: str,
    ) -> go.Bar:
        """Create a bar trace for the stacked bar chart.

        Args:
            data: DataFrame containing the visualization data.
            value_column: Name of the column containing values to plot.
            name: Name of the trace for the legend.
            color: Color for the bars.
            hover_template: Template for hover text.

        Returns:
            go.Bar: Configured bar trace.
        """
        values = data[value_column].multiply(100)
        return go.Bar(
            y=data["country"],
            x=values,
            name=name,
            orientation="h",
            marker_color=color,
            text=[f"{v:.1f}" if v > 0 else "" for v in values],
            textposition="inside",
            textfont=dict(color="white"),
            insidetextanchor="middle",
            hovertemplate=hover_template,
        )

    def _update_figure_layout(self, fig: go.Figure, num_countries: int) -> None:
        """Update the layout of the figure.

        Args:
            fig: Plotly figure object to update.
            num_countries: Number of countries in the visualization.
        """
        plot_height = max(
            self.PLOT_CONFIG["base_height"],
            num_countries * self.PLOT_CONFIG["height_per_country"],
        )

        fig.update_layout(
            title=dict(
                text=f"{self.PLOT_CONFIG['title']}<br>"
                f"<sub>Last updated: {LAST_UPDATE}, Sheet: Fig 14</sub>",
                font=dict(size=14),
                y=0.95,
                x=0.5,
                xanchor="center",
                yanchor="top",
            ),
            height=plot_height,
            margin=MARGIN,
            barmode="stack",
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            xaxis=dict(
                title="Percentage of National Stock",
                ticksuffix="%",
                showgrid=True,
                gridcolor="rgba(0,0,0,0.1)",
            ),
            yaxis=dict(
                title=None,
                autorange="reversed",
                showgrid=False,
                gridcolor="rgba(0,0,0,0.1)",
                zerolinecolor="rgba(0,0,0,0.2)",
                categoryorder="total descending",
            ),
            hovermode="y unified",
            plot_bgcolor="rgba(255,255,255,1)",
            paper_bgcolor="rgba(255,255,255,1)",
        )

    def register_outputs(self) -> None:
        """Register the plot output with Shiny."""

        @self.output
        @render_widget
        def pledges_weapon_types_plot() -> go.Figure:
            return self.create_plot()
