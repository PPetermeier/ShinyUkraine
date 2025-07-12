"""Module for visualizing total support allocation by donor region.

This module provides components for creating and managing an interactive visualization
that shows either monthly or cumulative support allocations across different donor
regions (United States, Europe, Rest of World) over time.
"""

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE, LAST_UPDATE, MARGIN
from server import TOTAL_SUPPORT_COLUMNS, load_time_series_data
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget


class TotalSupportCard:
    """UI components for the total support visualization card.

    This class handles the user interface elements for displaying and controlling
    the total support visualization, including the cumulative toggle.
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
                    {"class": "d-flex justify-content-between"},
                    ui.div(
                        {"class": "flex-grow-1"},
                        ui.h3(
                            "Monthly and cumulative bilateral aid allocation by donor"
                        ),
                        ui.div(
                            {"class": "card-subtitle text-muted"},
                            "This figure shows total bilateral aid allocations to Ukraine in € billion with traceable months between February 1, 2022 and August 31, 2024. Allocations are defined as aid which has been delivered or specified for delivery."
                            "Includes bilateral allocations to Ukraine. Allocations are defined as aid which has been "
                            "delivered or specified for delivery. Does not include private donations, support for refugees "
                            "outside of Ukraine, and aid by international organizations. Data on European Union aid include "
                            "the EU Commission and Council, EPF, and EIB. For information on data quality and transparency "
                            "please see our data transparency index."
                            "",
                        ),
                    ),
                    ui.div(
                        {"class": "d-flex align-items-center"},
                        "Cumulative",
                        ui.input_switch("total_support_additive", None, value=False),
                    ),
                ),
            ),
            output_widget("support_plot"),
            height="800px",
        )


class TotalSupportServer:
    """Server logic for the total support visualization.

    This class handles data processing and plot generation for both monthly and
    cumulative total support visualizations.

    Attributes:
        input: Shiny input object containing user interface values.
        output: Shiny output object for rendering visualizations.
        session: Shiny session object.
        df (pd.DataFrame): DataFrame containing total support time series data.
    """

    # Define region configurations
    REGIONS: dict[str, dict[str, str]] = {
        "united_states": {
            "column": "united_states_allocated__billion",
            "display_name": "United States",
            "color_key": "united_states",
        },
        "europe": {
            "column": "europe_allocated__billion",
            "display_name": "Europe",
            "color_key": "europe",
        },
        "other_donors": {
            "column": "other_donors_allocated__billion",
            "display_name": "Rest of World",
            "color_key": "other_donors",
        },
    }

    # Define visualization modes
    VIZ_CONFIGS: dict[str, dict[str, object]] = {
        "cumulative": {
            "title": "Cumulative Support Allocation Over Time",
            "mode": "lines",
            "line_width": 2,
            "bar_mode": None,
        },
        "monthly": {
            "title": "Monthly Support Allocation",
            "text_position": "inside",
            "text_color": "white",
            "text_anchor": "middle",
            "bar_mode": "group",
        },
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
        self.df = load_time_series_data(TOTAL_SUPPORT_COLUMNS)
        self._filtered_data = reactive.Calc(self._compute_filtered_data)
        self.register_outputs()

    def _compute_filtered_data(self) -> pd.DataFrame:
        """Compute filtered data based on user selections.

        Returns:
            pd.DataFrame: Filtered and processed DataFrame containing support data.
        """
        selected_cols = [config["column"] for config in self.REGIONS.values()]
        result = self.df[["month"] + selected_cols].copy()

        if self.input.total_support_additive():
            for col in selected_cols:
                result[col] = result[col].cumsum()
            result["total"] = result[selected_cols].sum(axis=1)

        return result

    def create_plot(self) -> go.Figure:
        """Generate the total support visualization plot.

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
            data: DataFrame containing filtered support data.

        Returns:
            go.Figure: Configured visualization figure.
        """
        fig = go.Figure()
        is_cumulative = self.input.total_support_additive()

        if is_cumulative:
            self._add_cumulative_traces(fig, data)
        else:
            self._add_monthly_traces(fig, data)

        return fig

    def _add_cumulative_traces(self, fig: go.Figure, data: pd.DataFrame) -> None:
        """Add cumulative area traces to the figure.

        Args:
            fig: Plotly figure to add traces to.
            data: DataFrame containing support data.
        """
        # Sort regions based on maximum values
        regions = sorted(
            self.REGIONS.keys(), key=lambda x: data[self.REGIONS[x]["column"]].max()
        )

        for region in regions:
            config = self.REGIONS[region]
            fig.add_trace(
                go.Scatter(
                    x=data["month"],
                    y=data[config["column"]],
                    name=config["display_name"],
                    stackgroup="one",
                    mode=self.VIZ_CONFIGS["cumulative"]["mode"],
                    line=dict(
                        color=COLOR_PALETTE[config["color_key"]],
                        width=self.VIZ_CONFIGS["cumulative"]["line_width"],
                    ),
                    hovertemplate=f"{config['display_name']}: %{{y:.1f}}B$<extra></extra>",
                )
            )

    def _add_monthly_traces(self, fig: go.Figure, data: pd.DataFrame) -> None:
        """Add monthly bar traces to the figure.

        Args:
            fig: Plotly figure to add traces to.
            data: DataFrame containing support data.
        """
        for region, config in self.REGIONS.items():
            fig.add_trace(
                go.Bar(
                    x=data["month"],
                    y=data[config["column"]],
                    name=config["display_name"],
                    marker_color=COLOR_PALETTE[config["color_key"]],
                    text=[f"{v:.1f}" if v > 0 else "" for v in data[config["column"]]],
                    textposition=self.VIZ_CONFIGS["monthly"]["text_position"],
                    textfont=dict(color=self.VIZ_CONFIGS["monthly"]["text_color"]),
                    insidetextanchor=self.VIZ_CONFIGS["monthly"]["text_anchor"],
                    hovertemplate=f"{config['display_name']}: %{{y:.1f}}B$<extra></extra>",
                )
            )

    def _update_figure_layout(self, fig: go.Figure) -> None:
        """Update the layout of the figure.

        Args:
            fig: Plotly figure object to update.
        """
        is_cumulative = self.input.total_support_additive()
        mode = "cumulative" if is_cumulative else "monthly"

        fig.update_layout(
            title=dict(
                text=f"{self.VIZ_CONFIGS[mode]['title']}<br>"
                f"<sub>Last updated: {LAST_UPDATE}, Sheet: Fig 1</sub>",
                font=dict(size=14),
                y=0.95,
                x=0.5,
                xanchor="center",
                yanchor="top",
            ),
            xaxis_title="Month",
            yaxis_title="Billion $",
            barmode=self.VIZ_CONFIGS[mode]["bar_mode"],
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
            ),
            showlegend=True,
            hovermode="x unified",
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

    def register_outputs(self) -> None:
        """Register the plot output with Shiny."""

        @self.output
        @render_widget
        def support_plot():
            return self.create_plot()
