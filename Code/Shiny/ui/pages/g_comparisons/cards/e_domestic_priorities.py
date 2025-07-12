"""Module for visualizing domestic support priorities comparisons.

This module provides components for creating and managing interactive visualizations
that compare different types of European support, including crisis responses,
domestic support vs Ukraine aid, and German spending programs.
"""

from typing import Any

import plotly.graph_objects as go
from config import COLOR_PALETTE, COMPARISONS_MARGIN, LAST_UPDATE
from server import load_data_from_table
from server.queries import (
    DOMESTIC_COMPARISON_QUERY,
    EUROPEAN_CRISIS_QUERY,
    GERMAN_COMPARISON_QUERY,
)
from shiny import ui
from shinywidgets import output_widget, render_widget


class DomesticPrioritiesCard:
    """UI components for the domestic priorities comparison visualization cards.

    This class handles the user interface elements for displaying three related
    visualizations comparing different aspects of European support.
    """

    @staticmethod
    def ui() -> ui.div:
        """Create the user interface elements for all visualization cards.

        Returns:
            ui.div: A Shiny div containing the visualization cards.
        """
        return ui.div(
            ui.div(
                {"class": "text-center mb-4"},
                ui.h3("Support Comparisons"),
                ui.div(
                    {"class": "text-muted"},
                    ui.HTML(
                        """Fig 1 compares the EU country’s total commitments to for Ukraine from Jan 24, 2022 to Aug 31, 2024 to the commitments announced during the Eurozone crisis (bailout funds for Greece, Ireland, Portugal and Spain 2020-12) and the EU Commission’s NGEU pandemic recovery fund announced July 2020.<br>

                    Fig 2 compares the amount of aid to Ukraine to the size of domestic spending programs of Germany, the UK, Italy, France, Netherlands, Spain, and an average across all EU member countries. The data on energy subsidy program commitments is taken from Bruegel (2022). Commitments to Ukraine cover January 24, 2022 and August 31, 2024 and include the shares of a country’s commitments through the EU. GDP data for 2021 is taken form the World Bank. Note that we sum up all commitments, including for payments that may lie several years in the future.<br>

                    Fig 3 compares German commitments to domestic spending packages announced since the start of the Russia-Ukraine war (February 2022) with Germany’s total support for Ukraine, both in billion Euros (light blue bars represent EU shares). For all, see Working Paper for relevant citations."""
                    ),
                ),
            ),
            ui.row(
                {"class": "g-4"},
                ui.column(
                    4,
                    ui.card(
                        {"class": "h-100"},
                        output_widget("crisis_comparison_plot", height="600px"),
                    ),
                ),
                ui.column(
                    4,
                    ui.card(
                        {"class": "h-100"},
                        ui.card_header(
                            ui.div(
                                {
                                    "class": "d-flex justify-content-between align-items-center"
                                },
                                ui.div(
                                    {"class": "ms-3"},
                                    ui.input_switch(
                                        "show_absolute_domestic_values",
                                        "Show Absolute Values",
                                        value=True,
                                    ),
                                ),
                            ),
                        ),
                        output_widget("domestic_support_plot", height="600px"),
                    ),
                ),
                ui.column(
                    4,
                    ui.card(
                        {"class": "h-100"},
                        output_widget("german_spending_plot", height="600px"),
                    ),
                ),
            ),
        )


class DomesticPrioritiesServer:
    """Server logic for the domestic priorities comparison visualizations.

    This class handles data processing, filtering, and plot generation for the
    three domestic priorities comparison visualizations.

    Attributes:
        input: Shiny input object containing user interface values.
        output: Shiny output object for rendering visualizations.
        session: Shiny session object.
        domestic_data: DataFrame containing domestic comparison data.
        crisis_data: DataFrame containing crisis comparison data.
        german_data: DataFrame containing German spending data.
    """

    # Define visualization properties
    PLOT_CONFIG: dict[str, Any] = {
        "height": 550,
        "title_font_size": 14,
        "subtitle_font_size": 12,
        "german_display_names": {
            'Energy subsidies for households and firms ("Doppelwumms")': "Energy Subsidies HHs & firms",
            'Special military fund ("Sondervermögen Bundeswehr") ': "Special Military Fund",
            "German aid to Ukraine": "Aid to Ukraine",
            "Rescue of Uniper (incl. EU shares)": "Rescue Uniper, total",
            'Transport Subsidies ("Tankrabatt" & "9€ Ticket")': "Transport Subsidies",
        },
        "legend_config": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.1,
            "xanchor": "center",
            "x": 0.5,
            "bgcolor": "rgba(255, 255, 255, 0.8)",
            "bordercolor": "rgba(0, 0, 0, 0.1)",
            "borderwidth": 1,
        },
        "axis_config": {
            "title": "",
            "categoryorder": "total ascending",
            "showticklabels": True,
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
        self.domestic_data = load_data_from_table(DOMESTIC_COMPARISON_QUERY)
        self.crisis_data = load_data_from_table(EUROPEAN_CRISIS_QUERY)
        self.german_data = load_data_from_table(GERMAN_COMPARISON_QUERY)

    def create_german_spending_plot(self) -> go.Figure:
        """Generate the German spending comparison plot.

        Returns:
            go.Figure: Plotly figure object containing the comparison visualization.
        """
        programs = self._prepare_german_data()
        fig = go.Figure()

        for program in programs:
            fig.add_trace(self._create_german_spending_trace(program))

        self._update_german_layout(fig)
        return fig

    def _prepare_german_data(self) -> list[dict[str, Any]]:
        """Prepare German spending data for visualization.

        Returns:
            List[Dict[str, Any]]: Processed program data.
        """
        return [
            {
                "name": self.PLOT_CONFIG["german_display_names"][row["commitments"]],
                "original_name": row["commitments"],
                "value": row["cost"] if row["cost"] > 0 else row["total_bilateral_aid"],
                "color": COLOR_PALETTE[row["commitments"]],
            }
            for row in self.german_data.to_dict("records")
        ]

    def create_crisis_comparison_plot(self) -> go.Figure:
        """Generate the crisis comparison plot.

        Returns:
            go.Figure: Plotly figure object containing the comparison visualization.
        """
        fig = go.Figure()

        for commitment, value in zip(
            self.crisis_data["commitments"],
            self.crisis_data["total_support__billion"],
            strict=False,
        ):
            fig.add_trace(self._create_crisis_trace(commitment, value))

        self._update_crisis_layout(fig)
        return fig

    def create_domestic_support_plot(self) -> go.Figure:
        """Generate the domestic support comparison plot.

        Returns:
            go.Figure: Plotly figure object containing the comparison visualization.
        """
        fig = go.Figure()
        display_config = self._get_domestic_display_config()

        self._add_domestic_traces(fig, display_config)
        self._update_domestic_layout(fig, display_config["y_axis_title"])

        return fig

    def _get_domestic_display_config(self) -> dict[str, Any]:
        """Get display configuration for domestic support visualization.

        Returns:
            Dict[str, Any]: Display configuration settings.
        """
        show_absolute = self.input.show_absolute_domestic_values()

        if show_absolute:
            return {
                "value_suffix": "B€",
                "y_axis_title": "Billion €",
                "fiscal_values": self.domestic_data["fiscal_abs"].tolist(),
                "ukraine_values": self.domestic_data["ukraine_abs"].tolist(),
            }
        return {
            "value_suffix": "%",
            "y_axis_title": "percent of GDP",
            "fiscal_values": self.domestic_data["fiscal_gdp"].tolist(),
            "ukraine_values": self.domestic_data["ukraine_gdp"].tolist(),
        }

    def _create_base_layout(self, title: str, sheet: str) -> dict[str, Any]:
        """Create base layout configuration for all plots.

        Args:
            title: Title for the plot.
            sheet: Sheet reference for the plot.

        Returns:
            Dict[str, Any]: Base layout configuration.
        """
        return {
            "height": self.PLOT_CONFIG["height"],
            "margin": COMPARISONS_MARGIN,
            "template": "plotly_white",
            "title": {
                "text": (
                    f"{title}<br>"
                    f"<span style='font-size: {self.PLOT_CONFIG['subtitle_font_size']}px; "
                    "color: gray;'>"
                    f"<br>Last updated: {LAST_UPDATE}, Sheet: {sheet}</span>"
                ),
                "x": 0.5,
                "y": 0.95,
            },
            "showlegend": True,
            "legend": self.PLOT_CONFIG["legend_config"],
            "yaxis": self.PLOT_CONFIG["axis_config"],
            "hovermode": "y unified",
        }

    def _create_german_spending_trace(self, program: dict[str, Any]) -> go.Bar:
        """Create a trace for German spending visualization.

        Args:
            program: Program data for the trace.

        Returns:
            go.Bar: Configured bar trace.
        """
        return go.Bar(
            y=[program["name"]],
            x=[program["value"]],
            orientation="h",
            name=program["name"],
            marker_color=program["color"],
            text=f"{program['value']:.1f}B€",
            textposition="auto",
            hovertemplate="%{y}<br>Amount: %{x:.1f}B€",
        )

    def _update_german_layout(self, fig: go.Figure) -> None:
        """Update layout for German spending visualization.

        Args:
            fig: Plotly figure to update.
        """
        base_layout = self._create_base_layout(
            "German Support Programs (2022)", "Fig 21"
        )
        base_layout.update({"xaxis_title": "Billion €", "barmode": "group"})
        fig.update_layout(**base_layout)

    def _create_crisis_trace(self, commitment: str, value: float) -> go.Bar:
        """Create a trace for crisis comparison visualization.

        Args:
            commitment: Commitment name.
            value: Support value.

        Returns:
            go.Bar: Configured bar trace.
        """
        return go.Bar(
            y=[commitment],
            x=[value],
            orientation="h",
            name=commitment,
            marker_color=COLOR_PALETTE[commitment],
            text=f"{value:.1f}B€",
            textposition="auto",
            hovertemplate="%{y}<br>Amount: %{x:.1f}B€",
        )

    def _update_crisis_layout(self, fig: go.Figure) -> None:
        """Update layout for crisis comparison visualization.

        Args:
            fig: Plotly figure to update.
        """
        base_layout = self._create_base_layout(
            "Europe's Response to Major Crises", "Fig 19"
        )
        base_layout.update({"xaxis_title": "Billion €"})
        fig.update_layout(**base_layout)

    def _add_domestic_traces(
        self, fig: go.Figure, display_config: dict[str, Any]
    ) -> None:
        """Add traces for domestic support visualization.

        Args:
            fig: Plotly figure to update.
            display_config: Display configuration settings.
        """
        countries = self.domestic_data["countries"].tolist()

        # Add fiscal commitments trace
        fig.add_trace(
            go.Bar(
                y=countries,
                x=display_config["fiscal_values"],
                name="Fiscal commitments for energy subsidies",
                marker_color=COLOR_PALETTE["Fiscal commitments for energy subsidies"],
                orientation="h",
                text=[
                    f"{x:.2f}{display_config['value_suffix']}"
                    for x in display_config["fiscal_values"]
                ],
                textposition="auto",
                customdata=list(
                    zip(
                        display_config["fiscal_values"],
                        display_config["ukraine_values"],
                        strict=False,
                    )
                ),
                hovertemplate=(
                    f"%{{y}}<br>"
                    f"Energy Subsidies: %{{customdata[0]:.2f}}{display_config['value_suffix']}<br>"
                    f"Ukraine Aid: %{{customdata[1]:.2f}}{display_config['value_suffix']}"
                ),
            )
        )

        # Add Ukraine aid trace
        fig.add_trace(
            go.Bar(
                y=countries,
                x=display_config["ukraine_values"],
                name="Aid for Ukraine (incl. EU share)",
                marker_color=COLOR_PALETTE["Aid for Ukraine (incl. EU share)"],
                orientation="h",
                text=[
                    f"{x:.2f}{display_config['value_suffix']}"
                    for x in display_config["ukraine_values"]
                ],
                textposition="auto",
                customdata=list(
                    zip(
                        display_config["fiscal_values"],
                        display_config["ukraine_values"],
                        strict=False,
                    )
                ),
                hovertemplate=(
                    f"%{{y}}<br>"
                    f"Energy Subsidies: %{{customdata[0]:.2f}}{display_config['value_suffix']}<br>"
                    f"Ukraine Aid: %{{customdata[1]:.2f}}{display_config['value_suffix']}"
                ),
            )
        )

    def _update_domestic_layout(self, fig: go.Figure, y_axis_title: str) -> None:
        """Update layout for domestic support visualization.

        Args:
            fig: Plotly figure to update.
            y_axis_title: Title for the y-axis.
        """
        base_layout = self._create_base_layout(
            "Domestic Energy Support vs Ukraine Aid", "Fig 20"
        )
        base_layout.update({"xaxis_title": y_axis_title, "barmode": "group"})
        fig.update_layout(**base_layout)

    def register_outputs(self) -> None:
        """Register all plot outputs with Shiny."""

        @self.output
        @render_widget
        def crisis_comparison_plot() -> go.Figure:
            return self.create_crisis_comparison_plot()

        @self.output
        @render_widget
        def domestic_support_plot() -> go.Figure:
            return self.create_domestic_support_plot()

        @self.output
        @render_widget
        def german_spending_plot() -> go.Figure:
            return self.create_german_spending_plot()
