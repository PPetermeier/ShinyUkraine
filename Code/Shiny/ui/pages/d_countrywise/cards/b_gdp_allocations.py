"""Module for visualizing aid allocations as a percentage of GDP.

This module provides components for creating and managing an interactive visualization
that compares bilateral aid, refugee costs, and EU share allocations as percentages
of each donor country's GDP.
"""

from typing import Dict, List

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE, LAST_UPDATE, MARGIN
from server import load_data_from_table
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget


class GDPAllocationsCard:
    """UI components for the GDP allocations visualization card.
    
    This class handles the user interface elements for displaying and controlling
    the GDP-relative aid allocation visualization.
    """

    @staticmethod
    def ui() -> ui.card:
        """Create the user interface elements for the visualization card.

        Returns:
            ui.card: A Shiny card containing the visualization and control elements.
        """
        return ui.card(
            ui.card_header(
                ui.h3("Support to Ukraine and Refugee Costs as Share of GDP"),
                ui.div(
                    {"class": "d-flex justify-content-between"},
                    ui.div(
                        {"class": "card-subtitle text-muted"},
                        "Includes bilateral allocations to Ukraine and cost estimates for refugees in donor countries. "
                        "Allocations are defined as aid which has been delivered or specified for delivery. Does not include "
                        "private donations, support for refugees outside of Ukraine, and aid by international organizations."
                        "These costs are based on estimates provided by the OECD Migration Outlook 2022 and scaled up using UNHCR refugee data. For further information, see the 'Refugee Cost Calculation' sheet.",
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
        )


class GDPAllocationsServer:
    """Server logic for the GDP allocations visualization.

    This class handles data processing, filtering, and plot generation for the
    GDP-relative aid allocation visualization.

    Attributes:
        input: Shiny input object containing user interface values.
        output: Shiny output object for rendering visualizations.
        session: Shiny session object.
        df (pd.DataFrame): DataFrame containing combined allocation and GDP data.
    """

    # Define allocation types and their properties
    ALLOCATION_TYPES: Dict[str, Dict[str, str]] = {
        "total_bilateral_allocations": {
            "name": "Total bilateral allocations",
            "color": "Total Bilateral",
            "hover_template": "Total bilateral allocations: %{x:.2f}% of GDP",
        },
        "refugee_cost_estimation": {
            "name": "Refugee cost estimation",
            "color": "refugee",
            "hover_template": "Refugee cost estimation: %{x:.2f}% of GDP",
        },
        "share_in_total_eu_allocations__2021_gdp": {
            "name": "Share in total EU allocations",
            "color": "europe",
            "hover_template": "Share in total EU allocations: %{x:.2f}% of GDP",
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
        self.df = self._load_and_merge_data()
        self._filtered_data = reactive.Calc(self._compute_filtered_data)
        self.register_outputs()

    def _load_and_merge_data(self) -> pd.DataFrame:
        """Load and merge allocation and summary data.

        Returns:
            pd.DataFrame: Merged DataFrame containing allocation and GDP data.
        """
        df_allocations = load_data_from_table("f_bilateral_allocations_gdp_pct")
        df_summary = load_data_from_table("a_summary_€")
        
        return pd.merge(
            df_allocations,
            df_summary[["country", "share_in_total_eu_allocations__2021_gdp"]],
            on="country",
            how="left"
        )

    def _compute_filtered_data(self) -> pd.DataFrame:
        """Filter and process data based on user selections.

        Returns:
            pd.DataFrame: Filtered and sorted DataFrame containing top N countries.
        """
        result = self.df.copy()
        allocation_cols = list(self.ALLOCATION_TYPES.keys())

        # Calculate total for sorting
        result["total"] = result[allocation_cols].sum(axis=1)

        # Get top N countries and sort
        result = result.nlargest(self.input.top_n_countries_gdp_ratio(), "total")
        result = result.sort_values("total", ascending=True)

        return result[["country"] + allocation_cols]

    def create_plot(self) -> go.Figure:
        """Generate the GDP allocations visualization plot.

        Returns:
            go.Figure: Plotly figure object containing the stacked bar chart.
        """
        data = self._filtered_data()
        if data.empty:
            return go.Figure()

        # Calculate dynamic height based on number of countries
        dynamic_height = max(400, len(data) * 40)
        
        # Create and configure plot
        fig = self._create_stacked_bar_chart(data, dynamic_height)
        
        return fig

    def _create_stacked_bar_chart(self, data: pd.DataFrame, height: int) -> go.Figure:
        """Create a stacked bar chart visualization.

        Args:
            data: DataFrame containing filtered allocation data.
            height: Height of the plot in pixels.

        Returns:
            go.Figure: Configured Plotly figure object.
        """
        fig = go.Figure()
        countries = data["country"].tolist()

        # Add traces for each allocation type
        for alloc_type, properties in self.ALLOCATION_TYPES.items():
            values = data[alloc_type].tolist()
            fig.add_trace(self._create_bar_trace(
                countries=countries,
                values=values,
                name=properties["name"],
                color=COLOR_PALETTE.get(properties["color"]),
                hover_template=properties["hover_template"]
            ))

        # Update layout
        self._update_figure_layout(fig, height)
        
        return fig

    def _create_bar_trace(
        self,
        countries: List[str],
        values: List[float],
        name: str,
        color: str,
        hover_template: str
    ) -> go.Bar:
        """Create a bar trace for the stacked bar chart.

        Args:
            countries: List of country names.
            values: List of values for the bars.
            name: Name of the allocation type.
            color: Color for the bars.
            hover_template: Template for hover text.

        Returns:
            go.Bar: Configured bar trace.
        """
        return go.Bar(
            y=countries,
            x=values,
            name=name,
            orientation="h",
            marker_color=color,
            hovertemplate=f"%{{y}}<br>{hover_template}<extra></extra>",
            text=[f"{v:.1f}" if v > 0 else "" for v in values],
            textposition="inside",
            textfont=dict(color="white"),
            insidetextanchor="middle",
        )

    def _update_figure_layout(self, fig: go.Figure, height: int) -> None:
        """Update the layout of the figure.

        Args:
            fig: Plotly figure object to update.
            height: Height of the plot in pixels.
        """
        fig.update_layout(
            title=dict(
                text=f"Bilateral Aid, Refugee Costs, and EU Share<br><sub>Last updated: {LAST_UPDATE}, Sheet: Summary(€), Fig 6</sub>",
                font=dict(size=14),
                y=0.95,
                x=0.5,
                xanchor="center",
                yanchor="top",
            ),
            xaxis_title="Percentage of 2021 GDP",
            barmode="stack",
            template="plotly_white",
            height=height,
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

    def register_outputs(self) -> None:
        """Register the plot output with Shiny."""
        @self.output
        @render_widget
        def gdp_allocations_plot():
            return self.create_plot()