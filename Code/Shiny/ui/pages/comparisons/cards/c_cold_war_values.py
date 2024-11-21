"""Module for visualizing US military support value comparisons.

This module provides components for creating and managing an interactive visualization
that compares historical US military expenditure across major conflicts with current
Ukraine support, showing both absolute values and GDP share comparisons.
"""

from typing import Any, Dict

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE, COMPARISONS_MARGIN, LAST_UPDATE
from server import load_data_from_table
from server.queries import US_WARS_COMPARISON_QUERY
from shiny import ui
from shinywidgets import output_widget, render_widget


class ColdWarCard:
    """UI components for the US military support comparison visualization card.

    This class handles the user interface elements for displaying the historical
    US military expenditure comparison visualization, including controls for
    switching between absolute values and GDP share views.
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
                        ui.h3("US Military Support Comparison"),
                        ui.div(
                            {"class": "card-subtitle text-muted mb-4"},
                            "This figure compares average annual US military expenditures in US wars to total US military aid to Ukraine between February 24, 2022 and August 31, 2024. Estimates on US military spending are from the US Congressional Research Service (Daggett 2010). US GDP Data is from the U.S. Bureau of Economic Analysis (2017) and IMF-WEO (2017). US military aid to Ukraine is from our database. For the sake of comparison, we only include aid to Ukraine from January 2022 to February 2023. See Working Paper for relevant citations.",
                        ),
                    ),
                    ui.div({"class": "ms-3"}, ui.input_switch("show_absolute_values", "Show Absolute Values", value=False)),
                ),
            ),
            output_widget("military_expenditure_plot", height="auto"),
        )


class ColdWarServer:
    """Server logic for the US military support comparison visualization.

    This class handles data processing, filtering, and plot generation for the
    historical US military support comparison visualization.

    Attributes:
        input: Shiny input object containing user interface values.
        output: Shiny output object for rendering visualizations.
        session: Shiny session object.
        expenditure_data: DataFrame containing the support comparison data.
    """

    # Define visualization properties
    PLOT_CONFIG: Dict[str, Any] = {
        "height": 700,
        "title_font_size": 16,
        "subtitle_font_size": 12,
        "value_format": {"absolute": "{:,.2f} €B", "relative": "{:,.2f}%"},
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
        self.expenditure_data = load_data_from_table(US_WARS_COMPARISON_QUERY)

    def _prepare_data(self) -> pd.DataFrame:
        """Process and prepare data for visualization.

        Returns:
            pd.DataFrame: Processed DataFrame containing support comparison data.
        """
        show_absolute = self.input.show_absolute_values()
        sort_column = "absolute_value" if show_absolute else "gdp_share"

        return self.expenditure_data.sort_values(by=sort_column, ascending=True)

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
        show_absolute = self.input.show_absolute_values()

        for _, row in data.iterrows():
            fig.add_trace(self._create_bar_trace(row, show_absolute))

        return fig

    def _create_bar_trace(self, row: pd.Series, show_absolute: bool) -> go.Bar:
        """Create a bar trace for a single conflict.

        Args:
            row: DataFrame row containing conflict data.
            show_absolute: Whether to show absolute values.

        Returns:
            go.Bar: Configured bar trace.
        """
        conflict_name = row["military_support"]
        legend_name = conflict_name.split("(")[0].strip()
        value = row["absolute_value"] if show_absolute else row["gdp_share"]

        return go.Bar(
            x=[value],
            y=[conflict_name],
            orientation="h",
            name=legend_name,
            marker_color=COLOR_PALETTE[conflict_name],
            text=[self.PLOT_CONFIG["value_format"]["absolute"].format(value) if show_absolute else self.PLOT_CONFIG["value_format"]["relative"].format(value)],
            textposition="auto",
            customdata=[[row["gdp_share"], row["absolute_value"]]],
            hovertemplate=("%{y}<br>" "GDP Share: %{customdata[0]:.2f}%<br>" "Amount: %{customdata[1]:.2f}€B"),
        )

    def _update_figure_layout(self, fig: go.Figure) -> None:
        """Update the layout of the figure.

        Args:
            fig: Plotly figure to update.
        """
        show_absolute = self.input.show_absolute_values()

        fig.update_layout(
            height=self.PLOT_CONFIG["height"],
            margin=COMPARISONS_MARGIN,
            xaxis_title="Billion 2021 Euros" if show_absolute else "% of US GDP",
            template="plotly_white",
            title=dict(
                text=(
                    "US Military Support Comparison<br>"
                    f"<span style='font-size: {self.PLOT_CONFIG['subtitle_font_size']}px; "
                    "color: gray;'>"
                    "This figure compares US military expenditure across major conflicts "
                    "with current Ukraine support."
                    f"<br>Last updated: {LAST_UPDATE}, Sheet: Fig 17</span>"
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
        def military_expenditure_plot() -> go.Figure:
            return self.create_plot()
