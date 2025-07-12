"""Module for visualizing financial aid distribution by type.

This module provides components for creating and managing an interactive visualization
that breaks down different types of financial aid (loans, grants, guarantees, swap lines)
provided by donor countries to Ukraine.
"""

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE, LAST_UPDATE, MARGIN
from server.database import load_data_from_table
from server.queries import FINANCIAL_AID_QUERY
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget


class FinancialByTypeCard:
    """UI components for the financial aid by type visualization card.

    This class handles the user interface elements for displaying and controlling
    the financial aid type visualization, including country selection.
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
                        ui.h3("Financial Bilateral Allocations by Type"),
                        ui.div(
                            {"class": "card-subtitle text-muted"},
                            "This figure shows financial aid allocations to Ukraine across the top 20 donors in billion Euros between January 24, 2022 and August 31, 2024. Financial aid includes loans, grants, guarantees, and central bank swap lines. "
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
                            None,
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
            height="1000px",
        )


class FinancialByTypeServer:
    """Server logic for the financial aid by type visualization.

    This class handles data processing, filtering, and plot generation for the
    financial aid type visualization.

    Attributes:
        input: Shiny input object containing user interface values.
        output: Shiny output object for rendering visualizations.
        session: Shiny session object.
    """

    # Define financial aid types and their properties
    FINANCIAL_AID_TYPES: dict[str, dict[str, str]] = {
        "loan": {
            "name": "Loan",
            "color_key": "financial_loan",
            "default_color": "#2a9d8f",
            "column": "loan",
            "hover_template": "Loan: %{x:.1f}B €",
        },
        "grant": {
            "name": "Grant",
            "color_key": "financial_grant",
            "default_color": "#264653",
            "column": "grant",
            "hover_template": "Grant: %{x:.1f}B €",
        },
        "guarantee": {
            "name": "Guarantee",
            "color_key": "financial_guarantee",
            "default_color": "#e9c46a",
            "column": "guarantee",
            "hover_template": "Guarantee: %{x:.1f}B €",
        },
        "central_bank_swap_line": {
            "name": "Central Bank Swap Line",
            "color_key": "financial_swap",
            "default_color": "#f4a261",
            "column": "central_bank_swap_line",
            "hover_template": "Central Bank Swap Line: %{x:.1f}B €",
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
        self._filtered_data = reactive.Calc(self._compute_filtered_data)

    def _compute_filtered_data(self) -> pd.DataFrame:
        """Compute filtered data based on user inputs.

        Returns:
            pd.DataFrame: Filtered and sorted DataFrame containing top N countries.
        """
        df = load_data_from_table(table_name_or_query=FINANCIAL_AID_QUERY)

        # Calculate total aid for sorting
        aid_columns = [props["column"] for props in self.FINANCIAL_AID_TYPES.values()]
        df["total_aid"] = df[aid_columns].sum(axis=1)

        # Filter to top N countries and sort
        df = df.nlargest(self.input.top_n_countries(), "total_aid")
        df = df.sort_values("total_aid", ascending=True)

        return df

    def create_plot(self) -> go.Figure:
        """Generate the financial aid type visualization plot.

        Returns:
            go.Figure: Plotly figure object containing the stacked bar chart.
        """
        data = self._filtered_data()
        if data.empty:
            return go.Figure()

        fig = self._create_stacked_bar_chart(data)
        return fig

    def _create_stacked_bar_chart(self, data: pd.DataFrame) -> go.Figure:
        """Create a stacked bar chart visualization.

        Args:
            data: DataFrame containing filtered financial aid data.

        Returns:
            go.Figure: Configured Plotly figure object.
        """
        fig = go.Figure()
        countries = data["country"].tolist()

        # Add traces for each financial aid type
        for aid_type, properties in self.FINANCIAL_AID_TYPES.items():
            fig.add_trace(
                self._create_bar_trace(
                    countries=countries,
                    values=data[properties["column"]].tolist(),
                    name=properties["name"],
                    color=COLOR_PALETTE.get(
                        properties["color_key"], properties["default_color"]
                    ),
                    hover_template=properties["hover_template"],
                )
            )

        # Update layout
        self._update_figure_layout(fig)

        return fig

    def _create_bar_trace(
        self,
        countries: list[str],
        values: list[float],
        name: str,
        color: str,
        hover_template: str,
    ) -> go.Bar:
        """Create a bar trace for the stacked bar chart.

        Args:
            countries: List of country names.
            values: List of values for the bars.
            name: Name of the financial aid type.
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
                text=f"Financial Bilateral Allocations by Type<br><sub>Last updated: {LAST_UPDATE}, Sheet: Fig 10</sub>",
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
            height=800,
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
        def financial_types_plot():
            return self.create_plot()
