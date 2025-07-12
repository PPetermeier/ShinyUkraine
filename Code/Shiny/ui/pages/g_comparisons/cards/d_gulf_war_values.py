"""Module for visualizing Gulf War and Ukraine aid value comparisons.

This module provides components for creating and managing an interactive visualization
that compares military expenditure during the Gulf War (1990/91) with current aid
to Ukraine, showing both absolute values and GDP share comparisons.
"""

from typing import Any

import plotly.graph_objects as go
from config import COLOR_PALETTE, COMPARISONS_MARGIN, LAST_UPDATE
from server import load_data_from_table
from server.queries import GULF_WAR_COMPARISON_QUERY
from shiny import ui
from shinywidgets import output_widget, render_widget


class GulfWarCard:
    """UI components for the Gulf War comparison visualization card.

    This class handles the user interface elements for displaying the Gulf War
    vs Ukraine aid comparison visualization, including controls for switching
    between absolute values and GDP share views.
    """

    @staticmethod
    def ui() -> ui.card:
        """Create the user interface elements for the visualization card.

        Returns:
            ui.card: A Shiny card containing the visualization and controls.
        """
        return ui.card(
            ui.card_header(
                ui.div(
                    {"class": "d-flex justify-content-between align-items-center"},
                    ui.div(
                        {"class": "flex-grow-1"},
                        ui.h3("Gulf War vs Ukraine Aid Comparison"),
                        ui.div(
                            {"class": "card-subtitle text-muted mb-4"},
                            "This figure compares the military expenditure of the US, Japan, Germany and South Korea in the Persian Gulf War with bilateral aid to Ukraine. For the sake of comparison, we only include aid to Ukraine from January 2022 to February 2023. See Working Paper for relevant citations.",
                        ),
                    ),
                    ui.div(
                        {"class": "ms-3"},
                        ui.input_switch(
                            "show_absolute_gulfwar_values",
                            "Show Absolute Values",
                            value=False,
                        ),
                    ),
                ),
            ),
            output_widget("gulf_war_plot", height="auto"),
        )


class GulfWarServer:
    """Server logic for the Gulf War comparison visualization.

    This class handles data processing, filtering, and plot generation for the
    Gulf War vs Ukraine aid comparison visualization.

    Attributes:
        input: Shiny input object containing user interface values.
        output: Shiny output object for rendering visualizations.
        session: Shiny session object.
        comparison_data: DataFrame containing the comparison data.
    """

    # Define visualization properties
    PLOT_CONFIG: dict[str, Any] = {
        "height": 700,
        "title_font_size": 16,
        "subtitle_font_size": 12,
        "traces": {
            "gulf_war": {
                "name": "Gulf War (1990/91)",
                "color": COLOR_PALETTE.get("Gulf War Percentage"),
                "columns": {"absolute": "gulf_war_abs", "relative": "gulf_war_gdp"},
            },
            "ukraine": {
                "name": "Aid to Ukraine",
                "color": COLOR_PALETTE.get("Ukraine Yellow"),
                "columns": {"absolute": "ukraine_abs", "relative": "ukraine_gdp"},
            },
        },
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
        self.comparison_data = load_data_from_table(GULF_WAR_COMPARISON_QUERY)

    def _get_display_config(self) -> dict[str, str]:
        """Get display configuration based on view type.

        Returns:
            Dict[str, str]: Configuration for display formatting.
        """
        show_absolute = self.input.show_absolute_gulfwar_values()

        if show_absolute:
            return {
                "title_suffix": "expenditures in Billion €",
                "y_axis_title": "Billion Euros (2021, inflation adjusted)",
                "value_suffix": "B€",
            }
        return {
            "title_suffix": "expenditures in percent of donor GDP",
            "y_axis_title": "% of donor GDP",
            "value_suffix": "%",
        }

    def create_plot(self) -> go.Figure:
        """Generate the comparison visualization plot.

        Returns:
            go.Figure: Plotly figure object containing the comparison visualization.
        """
        fig = self._create_bar_chart()
        self._update_figure_layout(fig)
        return fig

    def _create_bar_chart(self) -> go.Figure:
        """Create the bar chart visualization.

        Returns:
            go.Figure: Configured Plotly figure.
        """
        fig = go.Figure()
        display_config = self._get_display_config()

        for trace_type, config in self.PLOT_CONFIG["traces"].items():
            fig.add_trace(
                self._create_bar_trace(
                    trace_config=config, value_suffix=display_config["value_suffix"]
                )
            )

        return fig

    def _create_bar_trace(
        self, trace_config: dict[str, Any], value_suffix: str
    ) -> go.Bar:
        """Create a bar trace for the visualization.

        Args:
            trace_config: Configuration for the trace.
            value_suffix: Suffix for value labels.

        Returns:
            go.Bar: Configured bar trace.
        """
        show_absolute = self.input.show_absolute_gulfwar_values()
        column = (
            trace_config["columns"]["absolute"]
            if show_absolute
            else trace_config["columns"]["relative"]
        )

        values = self.comparison_data[column].tolist()

        return go.Bar(
            x=self.comparison_data["countries"].tolist(),
            y=values,
            name=trace_config["name"],
            marker_color=trace_config["color"],
            text=[f"{val:.2f}{value_suffix}" for val in values],
            textposition="auto",
            customdata=values,
            hovertemplate=(
                f"%{{x}}<br>{trace_config['name']}: %{{y:.2f}}{value_suffix}"
            ),
        )

    def _update_figure_layout(self, fig: go.Figure) -> None:
        """Update the layout of the figure.

        Args:
            fig: Plotly figure to update.
        """
        display_config = self._get_display_config()

        fig.update_layout(
            height=self.PLOT_CONFIG["height"],
            margin=COMPARISONS_MARGIN,
            xaxis_title=None,
            yaxis_title=display_config["y_axis_title"],
            template="plotly_white",
            title=dict(
                text=(
                    f"Gulf War 1990/91 vs. aid to Ukraine, {display_config['title_suffix']}<br>"
                    f"<span style='font-size: {self.PLOT_CONFIG['subtitle_font_size']}px; "
                    "color: gray;'>"
                    "This figure compares the Gulf War military expenditure with current "
                    "Ukraine support"
                    f"<br>Last updated: {LAST_UPDATE}. Sheet: Fig 18</span>"
                ),
                x=0.5,
                y=0.95,
                yanchor="top",
                xanchor="center",
                font=dict(size=self.PLOT_CONFIG["title_font_size"]),
                pad=dict(b=20),
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.12,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.2)",
                borderwidth=1,
                itemsizing="constant",
            ),
            showlegend=True,
            xaxis=dict(
                showgrid=False,
                gridcolor="rgba(0,0,0,0.1)",
                zeroline=True,
                zerolinecolor="rgba(0,0,0,0.2)",
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="rgba(0,0,0,0.1)",
                zeroline=True,
                zerolinecolor="rgba(0,0,0,0.2)",
            ),
            barmode="group",
            autosize=True,
            hovermode="x unified",
        )

    def register_outputs(self) -> None:
        """Register the plot output with Shiny."""

        @self.output
        @render_widget
        def gulf_war_plot() -> go.Figure:
            return self.create_plot()
