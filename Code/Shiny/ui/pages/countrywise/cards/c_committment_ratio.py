"""Module for visualizing aid allocation vs commitment ratios.

This module provides components for creating and managing an interactive visualization
that compares allocated aid against committed aid across different countries.
"""

from typing import Dict, List

import plotly.graph_objects as go
import pandas as pd
from config import COLOR_PALETTE, LAST_UPDATE, MARGIN
from server import load_data_from_table
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget


class CommittmentRatioCard:
    """UI components for the aid allocation visualization card.
    
    This class handles the user interface elements for displaying and controlling
    the aid allocation visualization, including filters and display options.
    """

    @staticmethod
    def ui() -> ui.card:
        """Create the user interface elements for the visualization card.

        Returns:
            ui.card: A Shiny card containing the visualization and control elements.
        """
        return ui.card(
            ui.card_header(
                ui.h3("Aid Allocation Progress"),
                ui.div(
                    {"class": "d-flex justify-content-between"},
                    ui.div(
                        {"class": "card-subtitle text-muted"},
                        "Includes bilateral allocations to Ukraine. Allocations are defined as aid "
                        "which has been delivered or specified for delivery. Does not include private donations, "
                        "support for refugees outside of Ukraine, and aid by international organizations.",
                    ),
                    ui.div(
                        {"class": "d-flex align-items-right gap-4"},
                        ui.div(
                            {"class": "d-flex align-items-center gap-2"},
                            "Percentage",
                            ui.input_switch("show_percentage_commitment_ratio", None, value=False),
                        ),
                        ui.panel_conditional(
                            "input.show_percentage_commitment_ratio",
                            ui.div(
                                {"class": "d-flex align-items-center gap-2"},
                                "Ascending",
                                ui.input_switch("reverse_sort_commitment_ratio", None, value=False),
                            ),
                        ),
                        ui.div(
                            {"class": "d-flex align-items-center"},
                            "First  ",
                            ui.input_numeric(
                                "top_n_countries_committment_ratio",
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
            ),
            output_widget("aid_allocation_plot"),
        )


class CommittmentRatioServer:
    """Server logic for the aid allocation visualization.

    This class handles data processing, filtering, and plot generation for the
    aid allocation visualization.

    Attributes:
        input: Shiny input object containing user interface values.
        output: Shiny output object for rendering visualizations.
        session: Shiny session object.
        df (pd.DataFrame): DataFrame containing aid allocation data.
    """

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
        self.df = self._prepare_initial_data()
        self._filtered_data = reactive.Calc(self._compute_filtered_data)
        self.register_outputs()

    def _prepare_initial_data(self) -> pd.DataFrame:
        """Prepare the initial dataset with calculated fields.

        Returns:
            pd.DataFrame: Processed DataFrame with additional calculated columns.
        """
        df = load_data_from_table("d_allocations_vs_commitments")
        if "allocated_aid" in df.columns and "committed_aid" in df.columns:
            df["to_be_allocated"] = df["committed_aid"] - df["allocated_aid"]
            df["delivery_ratio"] = df["allocated_aid"] / df["committed_aid"]
        return df

    def _compute_filtered_data(self) -> pd.DataFrame:
        """Filter and process data based on user selections.

        Returns:
            pd.DataFrame: Filtered and sorted DataFrame based on user inputs.
        """
        result = self.df.copy()
        show_percentage = self.input.show_percentage_commitment_ratio()
        reverse_sort = self.input.reverse_sort_commitment_ratio()

        if show_percentage:
            result["allocated_pct"] = (result["allocated_aid"] / result["committed_aid"]) * 100
            result["to_be_allocated_pct"] = (result["to_be_allocated"] / result["committed_aid"]) * 100
            ascending = not reverse_sort
            result = result.nlargest(self.input.top_n_countries_committment_ratio(), "committed_aid")
            result = result.sort_values("delivery_ratio", ascending=ascending)
        else:
            result = result.nlargest(self.input.top_n_countries_committment_ratio(), "committed_aid")
            result = result.sort_values("committed_aid", ascending=True)

        return result

    def create_plot(self) -> go.Figure:
        """Generate the aid allocation visualization plot.

        Returns:
            go.Figure: Plotly figure object containing the stacked bar chart.
        """
        data = self._filtered_data()
        if data.empty:
            return go.Figure()

        show_percentage = self.input.show_percentage_commitment_ratio()
        reverse_sort = self.input.reverse_sort_commitment_ratio()
        country_data = self._prepare_country_data(data, show_percentage)
        
        # Calculate dynamic height based on number of countries
        dynamic_height = max(400, len(data) * 40)
        
        # Create and configure plot
        fig = self._create_stacked_bar_chart(
            country_data,
            show_percentage,
            reverse_sort,
            dynamic_height
        )
        
        return fig

    def _prepare_country_data(self, data: pd.DataFrame, show_percentage: bool) -> Dict:
        """Prepare country-specific data for plotting.

        Args:
            data: DataFrame containing filtered aid data.
            show_percentage: Boolean indicating whether to show percentages.

        Returns:
            Dict: Processed country data ready for plotting.
        """
        country_data = {}
        for _, row in data.iterrows():
            if show_percentage:
                x_allocated = row["allocated_pct"]
                x_to_allocate = row["to_be_allocated_pct"]
            else:
                x_allocated = row["allocated_aid"]
                x_to_allocate = row["to_be_allocated"]

            country_data[row["country"]] = {
                "allocated": x_allocated,
                "to_allocate": x_to_allocate,
                "total": x_allocated + x_to_allocate,
            }
        return country_data

    def _create_stacked_bar_chart(
        self,
        country_data: Dict,
        show_percentage: bool,
        reverse_sort: bool,
        height: int
    ) -> go.Figure:
        """Create a stacked bar chart visualization.

        Args:
            country_data: Dictionary containing processed country data.
            show_percentage: Boolean indicating whether to show percentages.
            reverse_sort: Boolean indicating sort direction.
            height: Height of the plot in pixels.

        Returns:
            go.Figure: Configured Plotly figure object.
        """
        # Get colors from palette
        allocated_color = COLOR_PALETTE.get("aid_delivered", "#1f77b4")
        to_allocate_color = COLOR_PALETTE.get("aid_committed", "#ff7f0e")
        
        # Sort countries and prepare data
        sorted_countries = sorted(
            country_data.keys(),
            key=lambda x: country_data[x]["total"],
            reverse=reverse_sort if show_percentage else False
        )
        
        hover_suffix = "%" if show_percentage else " Billion €"
        
        # Create figure and add traces
        fig = go.Figure()
        
        allocated_values = [country_data[country]["allocated"] for country in sorted_countries]
        to_allocate_values = [country_data[country]["to_allocate"] for country in sorted_countries]
        
        # Add allocated aid trace
        fig.add_trace(self._create_bar_trace(
            sorted_countries,
            allocated_values,
            "Allocated aid",
            allocated_color,
            hover_suffix
        ))
        
        # Add to-be-allocated aid trace
        fig.add_trace(self._create_bar_trace(
            sorted_countries,
            to_allocate_values,
            "Aid to be allocated",
            to_allocate_color,
            hover_suffix
        ))
        
        # Update layout
        self._update_figure_layout(fig, show_percentage, height)
        
        return fig

    def _create_bar_trace(
        self,
        countries: List[str],
        values: List[float],
        name: str,
        color: str,
        hover_suffix: str
    ) -> go.Bar:
        """Create a bar trace for the stacked bar chart.

        Args:
            countries: List of country names.
            values: List of values for the bars.
            name: Name of the trace.
            color: Color for the bars.
            hover_suffix: Suffix for hover text.

        Returns:
            go.Bar: Configured bar trace.
        """
        return go.Bar(
            y=countries,
            x=values,
            name=name,
            orientation="h",
            marker_color=color,
            hovertemplate=f"%{{y}}<br>{name}: %{{x:.1f}}{hover_suffix}<extra></extra>",
            text=[f"{v:.1f}" if v > 0 else "" for v in values],
            textposition="inside",
            textfont=dict(color="white"),
            insidetextanchor="middle",
        )

    def _update_figure_layout(self, fig: go.Figure, show_percentage: bool, height: int) -> None:
        """Update the layout of the figure.

        Args:
            fig: Plotly figure object to update.
            show_percentage: Boolean indicating whether to show percentages.
            height: Height of the plot in pixels.
        """
        fig.update_layout(
            title=dict(
                text=f"Committed and allocated aid by country<br><sub>Last updated: {LAST_UPDATE}, Sheet: Fig 5</sub>",
                font=dict(size=14),
                y=0.95,
                x=0.5,
                xanchor="center",
                yanchor="top",
            ),
            barmode="stack",
            xaxis_title="Percent of Committed Aid" if show_percentage else "Billion €",
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
                range=[0, 100] if show_percentage else None,
            ),
            plot_bgcolor="rgba(255,255,255,1)",
            paper_bgcolor="rgba(255,255,255,1)",
        )

    def register_outputs(self) -> None:
        """Register the plot output with Shiny."""
        @self.output
        @render_widget
        def aid_allocation_plot():
            return self.create_plot()