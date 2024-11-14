"""
Financial aid by type visualization card.
"""

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE, LAST_UPDATE, MARGIN
from server.database import load_data_from_table
from server.queries import FINANCIAL_AID_QUERY
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget


class FinancialByTypeCard:
    """UI components for the financial aid by type visualization card."""

    @staticmethod
    def ui():
        """Return the card UI elements."""
        return ui.card(
            ui.card_header(
                ui.div(
                    {"class": "d-flex justify-content-between align-items-center"},
                    ui.div(
                        {"class": "flex-grow-1"},
                        ui.h3("Financial Bilateral Allocations by Type"),
                        ui.div(
                            {"class": "card-subtitle text-muted"},
                            "Includes bilateral financial commitments to Ukraine. Does not include private donations, "
                            "support for refugees outside of Ukraine, and aid by international organisations. "
                            "Commitments by EU Institutions include Commission and Council and EIB. "
                            "For information on data quality and transparency please see our data transparency index.",
                        ),
                    ),
                    ui.div(
                        {"class": "ms-3 d-flex align-items-center"},
                        ui.span({"class": "me-2"}, "First"),
                        ui.input_numeric(
                            "top_n_countries",
                            None,  # No label needed as it's inline
                            value=15,
                            min=5,
                            max=50,
                            width="80px",
                        ),
                        ui.span({"class": "ms-2"}, "countries"),
                    ),
                ),
            ),
            output_widget("financial_types_plot"),
            height="800px",
        )


class FinancialByTypeServer:
    """Server logic for the financial aid by type visualization card."""

    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
        self._filtered_data = reactive.Calc(self._compute_filtered_data)

    def _compute_filtered_data(self):
        """Internal method to compute filtered data based on user inputs."""
        # Load data using the predefined query
        df = load_data_from_table(table_name_or_query=FINANCIAL_AID_QUERY)

        # Calculate total aid for sorting
        df["total_aid"] = df.iloc[:, 1:].sum(axis=1)
        df = df.nlargest(self.input.top_n_countries(), "total_aid")
        df = df.sort_values("total_aid", ascending=True)  # For bottom-to-top display

        return df

    def create_plot(self):
        """Create and return the plot figure."""
        data = self._filtered_data()
        if data.empty:
            return go.Figure()

        fig = go.Figure()

        # Color mapping using the color palette
        color_mapping = {
            "loan": COLOR_PALETTE["financial_loan"],
            "grant": COLOR_PALETTE["financial_grant"],
            "guarantee": COLOR_PALETTE["financial_guarantee"],
            "central_bank_swap_line": COLOR_PALETTE["financial_swap"],
        }

        # Nice labels for the legend
        label_mapping = {"loan": "Loan", "grant": "Grant", "guarantee": "Guarantee", "central_bank_swap_line": "Central Bank Swap Line"}

        # Add bars for each type of aid
        for col in ["loan", "grant", "guarantee", "central_bank_swap_line"]:
            fig.add_trace(
                go.Bar(
                    name=label_mapping.get(col, col),
                    y=data["country"],
                    x=data[col],
                    orientation="h",
                    marker_color=color_mapping.get(col, "#000000"),
                    hovertemplate="%{y}<br>" + "%{customdata}<br>" + "Value: %{x:.1f}B €<extra></extra>",
                    customdata=[label_mapping.get(col, col)] * len(data),
                )
            )
        title = "Financial Bilateral Allocations by Type"
        fig.update_layout(
            title=dict(
                text=f"{title}<br><sub>Last updated: {LAST_UPDATE}, Sheet: Fig 10</sub>",
                font=dict(size=14),
                y=0.95,
                x=0.5,
                xanchor="center",
                yanchor="top",
            ),
            xaxis_title="Billion €",
            yaxis_title="",
            barmode="stack",
            template="plotly_white",
            height=600,
            margin=MARGIN,
            legend=dict(yanchor="bottom", y=0.01, xanchor="right", x=0.99, bgcolor="rgba(255, 255, 255, 0.8)", bordercolor="rgba(0, 0, 0, 0.2)", borderwidth=1),
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
        def financial_types_plot():
            return self.create_plot()
