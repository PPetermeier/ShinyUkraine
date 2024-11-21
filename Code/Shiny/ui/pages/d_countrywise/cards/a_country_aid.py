"""Module for visualizing bilateral aid distribution by country and type.

This module provides components for creating and managing an interactive visualization
that breaks down different types of aid (financial, humanitarian, military, refugee support)
provided by each donor country.
"""

from typing import Dict, List

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE, LAST_UPDATE, MARGIN
from server import load_country_data
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget


class CountryAidCard:
    """UI components for the country aid visualization card.
    
    This class handles the user interface elements for displaying and controlling
    the country aid visualization, including country selection options.
    """

    @staticmethod
    def ui() -> ui.card:
        """Create the user interface elements for the visualization card.

        Returns:
            ui.card: A Shiny card containing the visualization and control elements.
        """
        return ui.card(
            ui.card_header(
                ui.h3("Bilateral aid by country and type"),
                ui.div(
                    {"class": "d-flex justify-content-between"},
                    ui.div(
                        {"class": "card-subtitle text-muted"},
                        "This figure shows total bilateral aid allocations to Ukraine across donors in billion Euros between January 24, 2022 to August 31, 2024. Allocations are defined as aid which has been delivered or specified for delivery. Each bar shows the type of assistance"
                        "These costs are based on estimates provided by the OECD Migration Outlook 2022 and scaled up using UNHCR refugee data. For further information, see the 'Refugee Cost Calculation' sheet."
                        "Includes bilateral allocations to Ukraine and cost estimates for refugees in donor countries."
                        "Allocations are defined as aid which has been delivered or specified for delivery. Does not include "
                        "private donations, support for refugees outside of Ukraine, and aid by international organizations. "
                        "Data on European Union aid include the EU Commission and Council, EPF, and EIB. For information on "
                        "data quality and transparency please see our data transparency index.",
                    ),
                    ui.div(
                        {"class": "d-flex align-items-center"},
                        "First  ",
                        ui.input_numeric(
                            "top_n_countries_total_aid",
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
            output_widget("country_aid_plot"),
        )


class CountryAidServer:
    """Server logic for the country aid visualization.

    This class handles data processing, filtering, and plot generation for the
    country aid type visualization.

    Attributes:
        input: Shiny input object containing user interface values.
        output: Shiny output object for rendering visualizations.
        session: Shiny session object.
        df (pd.DataFrame): DataFrame containing country aid data.
    """

    # Define aid type configurations as a class constant
    AID_TYPES: Dict[str, Dict[str, str]] = {
        "financial": {"color": "financial", "name": "Financial"},
        "humanitarian": {"color": "humanitarian", "name": "Humanitarian"},
        "military": {"color": "military", "name": "Military"},
        "refugee_cost_estimation": {"color": "refugee", "name": "Refugee Support"},
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
        self.df = load_country_data()
        self._filtered_data = reactive.Calc(self._compute_filtered_data)
        self.register_outputs()

    def _compute_filtered_data(self) -> pd.DataFrame:
        """Filter and process data based on user selections.

        Returns:
            pd.DataFrame: Filtered and sorted DataFrame containing aid data for top N countries.
        """
        # Get list of aid type columns
        aid_cols = list(self.AID_TYPES.keys())

        # Create copy and calculate totals
        result = self.df.copy()
        result["total_aid"] = result[aid_cols].sum(axis=1)

        # Filter to top N countries and sort
        result = result.nlargest(self.input.top_n_countries_total_aid(), "total_aid")
        result = result.sort_values("total_aid", ascending=True)

        return result[["country"] + aid_cols]

    def create_plot(self) -> go.Figure:
        """Generate the country aid visualization plot.

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
            data: DataFrame containing filtered aid data.
            height: Height of the plot in pixels.

        Returns:
            go.Figure: Configured Plotly figure object.
        """
        fig = go.Figure()
        countries = data["country"].tolist()

        # Add bars for each aid type
        for aid_type, properties in self.AID_TYPES.items():
            values = data[aid_type].tolist()
            fig.add_trace(self._create_bar_trace(
                countries=countries,
                values=values,
                name=properties["name"],
                color=COLOR_PALETTE.get(properties["color"])
            ))

        # Update layout
        self._update_figure_layout(fig, height)
        
        return fig

    def _create_bar_trace(
        self,
        countries: List[str],
        values: List[float],
        name: str,
        color: str
    ) -> go.Bar:
        """Create a bar trace for the stacked bar chart.

        Args:
            countries: List of country names.
            values: List of values for the bars.
            name: Name of the aid type.
            color: Color for the bars.

        Returns:
            go.Bar: Configured bar trace.
        """
        return go.Bar(
            y=countries,
            x=values,
            name=name,
            orientation="h",
            marker_color=color,
            hovertemplate=f"%{{y}}<br>{name}: %{{x:.1f}} Billion €<extra></extra>",
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
                text=f"Aid Allocation and Refugee Support Cost by Country and Type<br><sub>Last updated: {LAST_UPDATE}, Sheet: Fig 6</sub>",
                font=dict(size=14),
                y=0.95,
                x=0.5,
                xanchor="center",
                yanchor="top",
            ),
            xaxis_title="Billion €",
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
            ),
            plot_bgcolor="rgba(255,255,255,1)",
            paper_bgcolor="rgba(255,255,255,1)",
        )

    def register_outputs(self) -> None:
        """Register the plot output with Shiny."""
        @self.output
        @render_widget
        def country_aid_plot():
            return self.create_plot()