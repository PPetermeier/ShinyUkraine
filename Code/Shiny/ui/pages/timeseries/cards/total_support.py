"""
Total support visualization card.
"""

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE, LAST_UPDATE, MARGIN
from server import TOTAL_SUPPORT_COLUMNS, load_time_series_data
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget


class TotalSupportCard:
    """UI components for the total support card."""

    @staticmethod
    def ui():
        """Return the card UI elements."""
        return ui.card(
            ui.card_header(
                ui.div(
                    {"class": "d-flex justify-content-between"},
                    ui.div(
                        {"class": "flex-grow-1"},
                        ui.h3("Monthly and cumulative bilateral aid allocation by donor"),
                        ui.div(
                            {"class": "card-subtitle text-muted"},
                            "Includes bilateral allocations to Ukraine. Allocations are defined as aid which has been "
                            "delivered or specified for delivery. Does not include private donations, support for refugees "
                            "outside of Ukraine, and aid by international organizations. Data on European Union aid include "
                            "the EU Commission and Council, EPF, and EIB. For information on data quality and transparency "
                            "please see our data transparency index.",
                        ),
                    ),
                    ui.div(
                        {"class": "d-flex align-items-center"},
                        "Cumulative",
                        ui.input_switch("total_support_additive", None, value=False),
                    ),
                ),
            ),
            output_widget("support_plot"),
            height="800px",
        )


class TotalSupportServer:
    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
        self.df = load_time_series_data(TOTAL_SUPPORT_COLUMNS)
        self._filtered_data = reactive.Calc(self._compute_filtered_data)
        self.register_outputs()

    def _compute_filtered_data(self):
        """Internal method to compute filtered data."""
        selected_cols = ["united_states_allocated__billion", "europe_allocated__billion"]

        # Use all available data
        filtered_df = self.df.copy()

        result = filtered_df[["month"] + selected_cols]

        if self.input.total_support_additive():
            for col in selected_cols:
                result[col] = result[col].cumsum()

            # Calculate total for both regions
            result["total"] = result[selected_cols].sum(axis=1)

        return result

    def create_plot(self):
        """Create and return the plot figure."""
        data = self._filtered_data()
        if data.empty:
            return go.Figure()

        if self.input.total_support_additive():
            fig = go.Figure()

            regions = ["united_states", "europe"]
            # Sort regions based on maximum values
            regions = sorted(regions, key=lambda x: data[f"{x}_allocated__billion"].max())

            # Plot the smaller value first
            for i, region in enumerate(regions):
                col_name = f"{region}_allocated__billion"
                name = "United States" if region == "united_states" else "Europe"

                fig.add_trace(
                    go.Scatter(
                        x=data["month"],
                        y=data[col_name],
                        name=name,
                        fill="tonexty" if i > 0 else "tozeroy",
                        mode="lines",
                        line=dict(color=COLOR_PALETTE[region], width=2),
                        stackgroup="one",
                        hovertemplate="%{y:.1f}B $<extra></extra>",
                    )
                )

            title = "Cumulative Support Allocation Over Time"

        else:
            fig = go.Figure()

            for region in ["united_states", "europe"]:
                col_name = f"{region}_allocated__billion"
                fig.add_trace(
                    go.Bar(
                        x=data["month"], y=data[col_name], name="United States" if region == "united_states" else "Europe", marker_color=COLOR_PALETTE[region]
                    )
                )

            title = "Monthly Support Allocation"

        fig.update_layout(
            title=dict(text=f"{title}<br><sub>Last updated: {LAST_UPDATE}</sub>", font=dict(size=14), y=0.95, x=0.5, xanchor="center", yanchor="top"),
            xaxis_title="Month",
            yaxis_title="Billion $",
            barmode="group",
            template="plotly_white",
            height=600,
            margin=MARGIN,
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            showlegend=True,
            hovermode="x unified",
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
            ),
            plot_bgcolor="rgba(255,255,255,1)",
            paper_bgcolor="rgba(255,255,255,1)",
        )
        fig.data = list(fig.data[:-1]) + [fig.data[-1]]
        return fig

    def register_outputs(self):
        """Register all outputs for the module."""

        @self.output
        @render_widget
        def support_plot():
            return self.create_plot()
