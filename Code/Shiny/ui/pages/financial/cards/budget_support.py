"""
Budget support allocations vs disbursements visualization card.
"""

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE, LAST_UPDATE, MARGIN
from server.database import load_data_from_table
from server.queries import BUDGET_SUPPORT_QUERY
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget


class BudgetSupportCard:
    """UI components for the budget support visualization card."""

    @staticmethod
    def ui():
        """Return the card UI elements."""
        return ui.card(
            ui.card_header(
                ui.div(
                    {"class": "d-flex justify-content-between align-items-center"},
                    ui.div(
                        {"class": "flex-grow-1"},
                        ui.h3("Foreign Budgetary Support: Allocations vs. Disbursements"),
                        ui.div(
                            {"class": "card-subtitle text-muted"},
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
                            None,  # No label needed as it's inline
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
    """Server logic for the budget support visualization card."""

    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
        self._filtered_data = reactive.Calc(self._compute_filtered_data)

    def _compute_filtered_data(self):
        """Internal method to compute filtered data based on user inputs."""
        # Load data using the predefined query
        df = load_data_from_table(table_name_or_query=BUDGET_SUPPORT_QUERY)

        # Rename columns for consistency with the visualization
        df = df.rename(columns={"allocations_loans_grants_and_guarantees": "allocations"})

        # Sort by allocations and get top N
        df = df.nlargest(self.input.top_n_donors(), "allocations")
        df = df.sort_values("allocations", ascending=True)  # For bottom-to-top display

        return df

    def create_plot(self):
        """Create and return the plot figure."""
        data = self._filtered_data()

        if data.empty:
            return go.Figure()

        fig = go.Figure()

        # Add bars for disbursements first (typically smaller values)
        fig.add_trace(
            go.Bar(
                name="Disbursements",
                y=data["country"],
                x=data["disbursements"],
                orientation="h",
                marker_color=COLOR_PALETTE.get("financial_disbursements", "#264653"),
                hovertemplate="%{y}<br>" + "Disbursements: %{x:.1f}B €<extra></extra>",
                text=[f"{v:.1f}" if v > 0 else "" for v in data["disbursements"]],
                textposition="inside",
                textfont=dict(color="white"),
                insidetextanchor="middle",
            )
        )

        # Add bars for allocations second (typically larger values)
        fig.add_trace(
            go.Bar(
                name="Allocations",
                y=data["country"],
                x=data["allocations"],
                orientation="h",
                marker_color=COLOR_PALETTE.get("financial_allocations"),
                hovertemplate="%{y}<br>" + "Allocations: %{x:.1f}B €<extra></extra>",
                text=[f"{v:.1f}" if v > 0 else "" for v in data["allocations"]],
                textposition="inside",
                textfont=dict(color="white"),
                insidetextanchor="middle",
            ),
        )

        title = "Allocations and Disbursements by country"
        fig.update_layout(
            title=dict(
                text=f"{title}<br><sub>Last updated: {LAST_UPDATE}, Sheet: Fig 11</sub>",
                font=dict(size=14),
                y=0.95,
                x=0.5,
                xanchor="center",
                yanchor="top"
            ),
            xaxis_title="Billion €",
            yaxis_title="",
            barmode="group",  # Changed from "overlay" to "group"
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
        return fig

    def register_outputs(self):
        """Register all outputs for the module."""

        @self.output
        @render_widget
        def budget_support_plot():
            return self.create_plot()
