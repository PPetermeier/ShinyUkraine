"""Module for visualizing heavy weapons deliveries to Ukraine.

This module provides components for creating and managing an interactive visualization
that shows the delivery of heavy weapons to Ukraine by country, measured in estimated
value (billion euros). It includes both UI components and server-side logic for data
processing and visualization.
"""

from typing import Any

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE, LAST_UPDATE, MARGIN
from server.database import load_data_from_table
from server.queries import HEAVY_WEAPONS_DELIVERY_QUERY
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget


class HeavyWeaponsCard:
    """UI components for the heavy weapons delivery visualization card.

    This class handles the user interface elements for displaying and controlling
    the heavy weapons delivery visualization, including country selection and
    filtering options.
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
                        ui.h3("Heavy Weapons Deliveries"),
                        ui.div(
                            {"class": "card-subtitle text-muted"},
                            "This figure shows estimated values of heavy weapon allocations to Ukraine across the top 20 donors in billion Euros between January 24, 2022 and August 31, 2024. Does not include ammunition of any kind, smaller arms or equipment, and funds committed for future weapons purchases. Allocations are defined as aid which has been delivered or specified for delivery. The values are calculated based on allocated units and our own price estimates for heavy weaponry. Therefore, the values displayed in this figure may not correspond to the amount of military aid displayed in Figure 8.",
                        ),
                    ),
                    ui.div(
                        {"class": "ms-3 d-flex align-items-center"},
                        ui.span({"class": "me-2"}, "Top"),
                        ui.input_numeric(
                            "top_n_countries_heavy_weapons",
                            None,
                            value=15,
                            min=5,
                            max=30,
                            width="80px",
                        ),
                        ui.span({"class": "ms-2"}, "countries"),
                    ),
                ),
            ),
            output_widget("heavy_weapons_plot"),
            height="800px",
        )


class HeavyWeaponsServer:
    """Server logic for the heavy weapons delivery visualization.

    This class handles data processing, filtering, and plot generation for the
    heavy weapons delivery visualization comparing different countries' contributions.

    Attributes:
        input: Shiny input object containing user interface values.
        output: Shiny output object for rendering visualizations.
        session: Shiny session object.
    """

    # Define visualization properties
    PLOT_CONFIG: dict[str, dict] = {
        "marker_color": COLOR_PALETTE.get("military", "#264653"),
        "hover_template": "%{y}<br>Value Estimate: %{x:.1f}B €<extra></extra>",
        "title": "Estimated Value of Heavy Weapons Delivered to Ukraine",
        "height": 600,
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
        df = load_data_from_table(table_name_or_query=HEAVY_WEAPONS_DELIVERY_QUERY)

        # Sort by total deliveries and get top N countries
        df = df.nlargest(
            self.input.top_n_countries_heavy_weapons(), "value_estimates_heavy_weapons"
        )
        return df.sort_values("value_estimates_heavy_weapons", ascending=True)

    def create_plot(self) -> go.Figure:
        """Generate the heavy weapons delivery visualization plot.

        Returns:
            go.Figure: Plotly figure object containing the bar chart.
        """
        data = self._filtered_data()
        if data.empty:
            return go.Figure()

        fig = self._create_bar_chart(data)
        self._update_figure_layout(fig)
        return fig

    def _create_bar_chart(self, data: pd.DataFrame) -> go.Figure:
        """Create a horizontal bar chart visualization.

        Args:
            data: DataFrame containing filtered heavy weapons delivery data.

        Returns:
            go.Figure: Configured Plotly figure object.
        """
        fig = go.Figure()
        fig.add_trace(self._create_bar_trace(data))
        return fig

    def _create_bar_trace(self, data: pd.DataFrame) -> go.Bar:
        """Create a bar trace for the horizontal bar chart.

        Args:
            data: DataFrame containing the visualization data.

        Returns:
            go.Bar: Configured bar trace.
        """
        return go.Bar(
            x=data["value_estimates_heavy_weapons"],
            y=data["country"],
            orientation="h",
            marker_color=self.PLOT_CONFIG["marker_color"],
            hovertemplate=self.PLOT_CONFIG["hover_template"],
            text=[
                f"{v:.1f}" if v > 0 else ""
                for v in data["value_estimates_heavy_weapons"]
            ],
            textposition="inside",
            textfont=dict(color="white"),
            insidetextanchor="middle",
        )

    def _update_figure_layout(self, fig: go.Figure) -> None:
        """Update the layout of the figure.

        Args:
            fig: Plotly figure object to update.
        """
        fig.update_layout(
            title=dict(
                text=f"{self.PLOT_CONFIG['title']}<br>"
                f"<sub>Last updated: {LAST_UPDATE}, Sheet: Fig 9</sub>",
                font=dict(size=14),
                y=0.95,
                x=0.5,
                xanchor="center",
                yanchor="top",
            ),
            xaxis_title="Billion €",
            yaxis_title="",
            template="plotly_white",
            height=self.PLOT_CONFIG["height"],
            margin=MARGIN,
            legend=dict(
                yanchor="bottom",
                y=0.01,
                xanchor="right",
                x=0.99,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0,0,0,0.2)",
                borderwidth=1,
            ),
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

    def register_outputs(self) -> None:
        """Register the plot output with Shiny."""

        @self.output
        @render_widget
        def heavy_weapons_plot() -> go.Figure:
            return self.create_plot()
