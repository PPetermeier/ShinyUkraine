"""Module for visualizing budget support allocations and disbursements.

This module provides components for creating and managing an interactive visualization
that compares allocated budget support against actual disbursements for different
donor countries supporting Ukraine.
"""

from typing import Dict, List

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE, LAST_UPDATE, MARGIN
from server.database import load_data_from_table
from server.queries import BUDGET_SUPPORT_QUERY
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget


class BudgetSupportCard:
    """UI components for the budget support visualization card.
    
    This class handles the user interface elements for displaying and controlling
    the budget support visualization, including donor country selection.
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
                        ui.h3("Foreign Budgetary Support: Allocations vs. Disbursements"),
                        ui.div(
                            {"class": "card-subtitle text-muted"},
                            "This figure shows a ranking of financial donors, measured by the nominal value of external grants, loans, and guarantees given for budgetary support to the government of Ukraine (in billion Euros). Light blue bars indicate allocations (Ukraine Support Tracker data), while the darker blue bars show disbursements (Ministry of Finance of Ukraine data)."
                            "This figure shows financial donors measured by the nominal value of external grants, loans, "
                            "and guarantees given for budgetary support to the government of Ukraine (in billion Euros). "
                            "Information on disbursement is disclosed by the Ministry of Finance of Ukraine.",
                        ),
                    ),
                    ui.div(
                        {"class": "ms-3 d-flex align-items-center"},
                        ui.span({"class": "me-2"}, "First"),
                        ui.input_numeric(
                            "top_n_donors",
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
            output_widget("budget_support_plot"),
            height="1000px",
        )


class BudgetSupportServer:
    """Server logic for the budget support visualization.

    This class handles data processing, filtering, and plot generation for the
    budget support visualization comparing allocations and disbursements.

    Attributes:
        input: Shiny input object containing user interface values.
        output: Shiny output object for rendering visualizations.
        session: Shiny session object.
    """

    # Define support types and their properties
    SUPPORT_TYPES: Dict[str, Dict[str, str]] = {
        "disbursements": {
            "name": "Disbursements",
            "color": "financial_disbursements",
            "default_color": "#264653",
            "hover_template": "Disbursements: %{x:.1f}B €"
        },
        "allocations": {
            "name": "Allocations",
            "color": "financial_allocations",
            "default_color": "#2a9d8f",
            "hover_template": "Allocations: %{x:.1f}B €"
        }
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
        self._filtered_data = reactive.Calc(self._compute_filtered_data)

    def _compute_filtered_data(self) -> pd.DataFrame:
        """Compute filtered data based on user inputs.

        Returns:
            pd.DataFrame: Filtered and sorted DataFrame containing top N donors.
        """
        df = load_data_from_table(table_name_or_query=BUDGET_SUPPORT_QUERY)
        
        # Rename columns for consistency
        df = df.rename(columns={
            "allocations_loans_grants_and_guarantees": "allocations"
        })

        # Sort by allocations and get top N
        df = df.nlargest(self.input.top_n_donors(), "allocations")
        df = df.sort_values("allocations", ascending=True)

        return df

    def create_plot(self) -> go.Figure:
        """Generate the budget support visualization plot.

        Returns:
            go.Figure: Plotly figure object containing the grouped bar chart.
        """
        data = self._filtered_data()
        if data.empty:
            return go.Figure()

        fig = self._create_grouped_bar_chart(data)
        return fig

    def _create_grouped_bar_chart(self, data: pd.DataFrame) -> go.Figure:
        """Create a grouped bar chart visualization.

        Args:
            data: DataFrame containing filtered budget support data.

        Returns:
            go.Figure: Configured Plotly figure object.
        """
        fig = go.Figure()

        # Add traces for each support type
        for support_type, properties in self.SUPPORT_TYPES.items():
            fig.add_trace(self._create_bar_trace(
                countries=data["country"].tolist(),
                values=data[support_type].tolist(),
                name=properties["name"],
                color=COLOR_PALETTE.get(properties["color"], properties["default_color"]),
                hover_template=properties["hover_template"]
            ))

        # Update layout
        self._update_figure_layout(fig)
        
        return fig

    def _create_bar_trace(
        self,
        countries: List[str],
        values: List[float],
        name: str,
        color: str,
        hover_template: str
    ) -> go.Bar:
        """Create a bar trace for the grouped bar chart.

        Args:
            countries: List of country names.
            values: List of values for the bars.
            name: Name of the support type.
            color: Color for the bars.
            hover_template: Template for hover text.

        Returns:
            go.Bar: Configured bar trace.
        """
        return go.Bar(
            name=name,
            y=countries,
            x=values,
            orientation="h",
            marker_color=color,
            hovertemplate=f"%{{y}}<br>{hover_template}<extra></extra>",
            text=[f"{v:.1f}" if v > 0 else "" for v in values],
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
                text=f"Allocations and Disbursements by country<br><sub>Last updated: {LAST_UPDATE}, Sheet: Fig 11</sub>",
                font=dict(size=14),
                y=0.95,
                x=0.5,
                xanchor="center",
                yanchor="top"
            ),
            xaxis_title="Billion €",
            yaxis_title="",
            barmode="group",
            template="plotly_white",
            height=800,
            margin=MARGIN,
            legend=dict(
                yanchor="bottom",
                y=0.01,
                xanchor="right",
                x=0.99,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0,0,0,0.2)",
                borderwidth=1
            ),
            showlegend=True,
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
        def budget_support_plot():
            return self.create_plot()