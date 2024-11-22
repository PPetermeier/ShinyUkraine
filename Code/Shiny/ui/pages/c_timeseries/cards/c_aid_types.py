"""Module for visualizing aid allocation trends by type.

This module provides components for creating and managing an interactive visualization
that shows either monthly or cumulative aid allocations across different aid types
(military, financial, humanitarian) over time.
"""

from typing import Dict

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE, LAST_UPDATE, MARGIN
from server.database import AID_TYPES_COLUMNS, load_time_series_data
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget
from ....colorutilities import desaturate_color


class AidTypesCard:
    """UI components for the aid types visualization card.

    This class handles the user interface elements for displaying and controlling
    the aid types visualization, including the cumulative toggle.
    """

    @staticmethod
    def ui() -> ui.card:
        """Create the user interface elements for the visualization card.

        Returns:
            ui.card: A Shiny card containing the visualization and controls.
        """
        return ui.card(
            ui.card_header(
                ui.h3("Monthly and cumulative bilateral aid allocation by type"),
                ui.div(
                    {"class": "d-flex flex-row justify-content-between"},
                    ui.div(
                        {"class": "flex-grow-1 me-4"},
                        "This figure shows total bilateral aid allocations to Ukraine in € billion with traceable months between February 1, 2022 and August 31, 2024. Allocations are defined as aid which has been delivered or specified for delivery."
                        "Includes bilateral allocations to Ukraine. Allocations are defined as aid which has been "
                        "delivered or specified for delivery. Does not include private donations, support for refugees "
                        "outside of Ukraine, and aid by international organizations. Data on European Union aid include "
                        "the EU Commission and Council, EPF, and EIB. For information on data quality and transparency "
                        "please see our data transparency index.",
                    ),
                    ui.div(
                        {"class": "flex-shrink-0 d-flex align-items-center"},
                        ui.span({"class": "me-2"}, "Cumulative"),
                        ui.input_switch("aid_types_cumulative", None, value=False),
                    ),
                ),
            ),
            output_widget("aid_types_plot"),
            height="800px",
        )


class AidTypesServer:
    """Server logic for the aid types visualization.

    This class handles data processing and plot generation for both monthly and
    cumulative aid type visualizations.

    Attributes:
        input: Shiny input object containing user interface values.
        output: Shiny output object for rendering visualizations.
        session: Shiny session object.
        df (pd.DataFrame): DataFrame containing aid type time series data.
    """

    # Define aid type configurations
    AID_TYPES: Dict[str, Dict[str, str]] = {
        "military_aid_allocated__billion": {"display_name": "Military Aid", "color_key": "military", "sort_priority": 1},
        "financial_aid_allocated__billion": {"display_name": "Financial Aid", "color_key": "financial", "sort_priority": 2},
        "humanitarian_aid_allocated__billion": {"display_name": "Humanitarian Aid", "color_key": "humanitarian", "sort_priority": 3},
    }

    # Define visualization modes
    VIZ_CONFIGS: Dict[str, Dict[str, object]] = {
        "cumulative": {"title": "Cumulative Support Allocation Over Time", "mode": "lines", "line_width": 2, "desaturation_factor": 0.6},
        "monthly": {"title": "Monthly Support Allocation", "text_position": "inside", "text_color": "white", "text_anchor": "middle"},
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
        self.df = load_time_series_data(AID_TYPES_COLUMNS)
        self._filtered_data = reactive.Calc(self._compute_filtered_data)
        self.register_outputs()

    def _compute_filtered_data(self) -> pd.DataFrame:
        """Compute filtered data based on user selections.

        Returns:
            pd.DataFrame: Filtered and processed DataFrame containing aid type data.
        """
        result = self.df.copy()
        aid_columns = list(self.AID_TYPES.keys())
        result = result[["month"] + aid_columns]

        if self.input.aid_types_cumulative():
            for col in aid_columns:
                result[col] = result[col].cumsum()

        return result

    def create_plot(self) -> go.Figure:
        """Generate the aid types visualization plot.

        Returns:
            go.Figure: Plotly figure object containing either monthly bars or cumulative area chart.
        """
        data = self._filtered_data()
        if data.empty:
            return go.Figure()

        fig = self._create_visualization(data)
        self._update_figure_layout(fig)
        return fig

    def _create_visualization(self, data: pd.DataFrame) -> go.Figure:
        """Create the appropriate visualization based on user selection.

        Args:
            data: DataFrame containing filtered aid type data.

        Returns:
            go.Figure: Configured visualization figure.
        """
        fig = go.Figure()
        is_cumulative = self.input.aid_types_cumulative()

        if is_cumulative:
            self._add_cumulative_traces(fig, data)
        else:
            self._add_monthly_traces(fig, data)

        return fig

    def _add_cumulative_traces(self, fig: go.Figure, data: pd.DataFrame) -> None:
        """Add cumulative area traces to the figure.

        Args:
            fig: Plotly figure to add traces to.
            data: DataFrame containing aid data.
        """
        data_cols = [col for col in data.columns if col != "month"]
        sorted_cols = sorted(data_cols, key=lambda x: (self.AID_TYPES[x]["sort_priority"], data[x].max()))

        for i, col in enumerate(sorted_cols):
            config = self.AID_TYPES[col]
            color = COLOR_PALETTE[config["color_key"]]

            fig.add_trace(
                go.Scatter(
                    x=data["month"],
                    y=data[col],
                    name=config["display_name"],
                    stackgroup="one",
                    mode=self.VIZ_CONFIGS["cumulative"]["mode"],
                    line=dict(color=color, width=self.VIZ_CONFIGS["cumulative"]["line_width"]),
                    fill="tonexty" if i > 0 else "tozeroy",
                    fillcolor=desaturate_color(color, factor=self.VIZ_CONFIGS["cumulative"]["desaturation_factor"]),
                    hovertemplate=f"{config['display_name']}: %{{y:.1f}}B€<extra></extra>",
                )
            )

    def _add_monthly_traces(self, fig: go.Figure, data: pd.DataFrame) -> None:
        """Add monthly bar traces to the figure.

        Args:
            fig: Plotly figure to add traces to.
            data: DataFrame containing aid data.
        """
        for col, config in self.AID_TYPES.items():
            fig.add_trace(
                go.Bar(
                    x=data["month"],
                    y=data[col],
                    name=config["display_name"],
                    marker_color=COLOR_PALETTE[config["color_key"]],
                    hovertemplate=f"{config['display_name']}: %{{y:.1f}}B€<extra></extra>",
                    text=[f"{v:.1f}" if v > 0 else "" for v in data[col]],
                    textposition=self.VIZ_CONFIGS["monthly"]["text_position"],
                    textfont=dict(color=self.VIZ_CONFIGS["monthly"]["text_color"]),
                    insidetextanchor=self.VIZ_CONFIGS["monthly"]["text_anchor"],
                )
            )

    def _update_figure_layout(self, fig: go.Figure) -> None:
        """Update the layout of the figure.

        Args:
            fig: Plotly figure object to update.
        """
        is_cumulative = self.input.aid_types_cumulative()
        mode = "cumulative" if is_cumulative else "monthly"

        fig.update_layout(
            title=dict(
                text=f"{self.VIZ_CONFIGS[mode]['title']}<br>" f"<sub>Last updated: {LAST_UPDATE}, Sheet: Fig 1</sub>",
                font=dict(size=14),
                y=0.95,
                x=0.5,
                xanchor="center",
                yanchor="top",
            ),
            xaxis_title="Month",
            yaxis_title="Billion €",
            template="plotly_white",
            height=600,
            margin=MARGIN,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.2)",
                borderwidth=1,
                itemsizing="constant",
                tracegroupgap=5,
            ),
            showlegend=True,
            hovermode="x unified",
            autosize=True,
            width=None,
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
            barmode="stack" if not is_cumulative else None,
        )

    def register_outputs(self) -> None:
        """Register the plot output with Shiny."""

        @self.output
        @render_widget
        def aid_types_plot():
            return self.create_plot()
