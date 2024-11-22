"""Module for visualizing historical military support value comparisons.

This module provides components for creating and managing an interactive visualization
that compares military support values between WW2 Lend-Lease programs and current
Ukraine support, showing both absolute values and GDP share comparisons.
"""

from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE, COMPARISONS_MARGIN, LAST_UPDATE
from server import load_data_from_table
from server.queries import WW2_COMPARISON_QUERY
from shiny import ui
from shinywidgets import output_widget, render_widget


class WW2UkraineComparisonCard:
    """UI components for the WW2 vs Ukraine support comparison visualization card.

    This class handles the user interface elements for displaying the historical
    support comparison visualization, including controls for switching between
    absolute values and GDP share views.
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
                        ui.h3("Historical Military Support Comparison"),
                        ui.div(
                            {"class": "card-subtitle text-muted"},
                            "This figure compares the scale of foreign military support by the US and the UK during the Second World War (Lend-Lease program) to their military support to Ukraine between February 2022 and February 2023. We report total aid divided by the number of years during which aid was provided (WW2: 1941 to 1945). US and UK military aid to Ukraine is from our database. See Working Paper for relevant citations.",
                        ),
                    ),
                    ui.div({"class": "ms-3"}, ui.input_switch("show_absolute_ww2_values", "Show Absolute Values", value=False)),
                ),
            ),
            output_widget("support_comparison_plot"),
        )


class WW2UkraineComparisonServer:
    """Server logic for the WW2 vs Ukraine support comparison visualization.

    This class handles data processing, filtering, and plot generation for the
    historical support comparison visualization.

    Attributes:
        input: Shiny input object containing user interface values.
        output: Shiny output object for rendering visualizations.
        session: Shiny session object.
        comparison_data: DataFrame containing the support comparison data.
    """

    # Define visualization properties
    PLOT_CONFIG: Dict[str, Any] = {
        "height": 700,
        "legend_mapping": {
            "US support to UK": "WW2 US to UK",
            "US support to USSR": "WW2 US to USSR",
            "British support to USSR": "WW2 British to USSR",
            "US support to France": "WW2 US to France",
            "British military aid to Ukraine": "British to Ukraine",
            "US to Ukraine": "US to Ukraine",
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
        self.comparison_data = load_data_from_table(WW2_COMPARISON_QUERY)

    def _prepare_data(self) -> pd.DataFrame:
        """Process and prepare data for visualization.

        Returns:
            pd.DataFrame: Processed DataFrame containing support comparison data.
        """
        df = self.comparison_data.copy()
        show_absolute = self.input.show_absolute_ww2_values()

        # Sort by appropriate column
        sort_column = "absolute_value" if show_absolute else "gdp_share"
        df = df.sort_values(by=sort_column, ascending=True)

        # Map support names to legend names
        df["legend_name"] = df["military_support"].map(
            lambda x: next(
                (new for old, new in self.PLOT_CONFIG["legend_mapping"].items() if old in x),
                "US to Ukraine",  # Default fallback
            )
        )

        return df

    def create_plot(self) -> go.Figure:
        """Generate the support comparison visualization plot.

        Returns:
            go.Figure: Plotly figure object containing the comparison visualization.
        """
        df = self._prepare_data()
        fig = self._create_bar_chart(df)
        self._update_figure_layout(fig)
        return fig

    def _create_bar_chart(self, data: pd.DataFrame) -> go.Figure:
        """Create the bar chart visualization.

        Args:
            data: DataFrame containing the visualization data.

        Returns:
            go.Figure: Configured Plotly figure.
        """
        fig = go.Figure()
        show_absolute = self.input.show_absolute_ww2_values()

        for legend_name in data["legend_name"].unique():
            x_values = [None] * len(data)
            text_values = [None] * len(data)
            customdata = [[None, None, None]] * len(data)

            for idx, (_, row) in enumerate(data.iterrows()):
                if row["legend_name"] == legend_name:
                    value = row["absolute_value"] if show_absolute else row["gdp_share"]
                    x_values[idx] = value
                    text_values[idx] = f"{value:,.2f}{' €B' if show_absolute else '%'}"
                    customdata[idx] = [row["gdp_share"], row["absolute_value"], row["military_conflict"]]

            fig.add_trace(
                self._create_bar_trace(
                    x_values=x_values, y_values=data["military_support"], legend_name=legend_name, text_values=text_values, customdata=customdata
                )
            )

        return fig

    def _create_bar_trace(
        self, x_values: List[float], y_values: List[str], legend_name: str, text_values: List[str], customdata: List[List[Optional[float]]]
    ) -> go.Bar:
        """Create a bar trace for the visualization.

        Args:
            x_values: List of x-axis values.
            y_values: List of y-axis values.
            legend_name: Name for the legend.
            text_values: List of text values for labels.
            customdata: List of custom data for hover information.

        Returns:
            go.Bar: Configured bar trace.
        """
        return go.Bar(
            x=x_values,
            y=y_values,
            orientation="h",
            name=legend_name,
            marker_color=COLOR_PALETTE[legend_name],
            text=text_values,
            textposition="auto",
            customdata=customdata,
            hovertemplate=("%{y}<br>" "GDP Share: %{customdata[0]:.2f}%<br>" "Amount: %{customdata[1]:.2f}€B<br>" "Conflict: %{customdata[2]}"),
        )

    def _update_figure_layout(self, fig: go.Figure) -> None:
        """Update the layout of the figure.

        Args:
            fig: Plotly figure to update.
        """
        show_absolute = self.input.show_absolute_ww2_values()

        fig.update_layout(
            height=self.PLOT_CONFIG["height"],
            margin=COMPARISONS_MARGIN,
            xaxis_title="Billion 2022 Euros" if show_absolute else "% of donor GDP",
            template="plotly_white",
            title=dict(
                text=(
                    "Historical Military Support Comparison<br>"
                    "<span style='font-size: 12px; color: gray;'>"
                    "This figure compares military support across major conflicts, "
                    "showing both WW2 Lend-Lease and current Ukraine support."
                    f"<br>Last updated: {LAST_UPDATE}, Sheet: Fig 16</span>"
                ),
                x=0.5,
                y=0.98,
                xanchor="center",
                yanchor="top",
                font=dict(size=16),
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
            ),
            showlegend=True,
            xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.1)", zeroline=True, zerolinecolor="rgba(0,0,0,0.2)"),
            yaxis=dict(showticklabels=False, showgrid=False),
            barmode="overlay",
            autosize=True,
            hovermode="y unified",
        )

    def register_outputs(self) -> None:
        """Register the plot output with Shiny."""

        @self.output
        @render_widget
        def support_comparison_plot() -> go.Figure:
            return self.create_plot()
