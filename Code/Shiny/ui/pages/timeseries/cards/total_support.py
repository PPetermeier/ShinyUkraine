"""
Total support visualization card.
"""

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE
from server import load_time_series_data, TOTAL_SUPPORT_COLUMNS
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget


class TotalSupportCard:
    """UI components for the total support card."""

    @staticmethod
    def ui():
        """Return the card UI elements."""
        return ui.card(
            ui.card_header(ui.h3("Monthly and cumulative aid allocation by donor"), ui.div({"class": "card-subtitle text-muted"}, "Includes bilateral allocations to Ukraine. Allocations are defined as aid which has been delivered or specified for delivery. Does not include private donations, support for refugees outside of Ukraine, and aid by international organizations. Data on European Union aid include the EU Commission and Council, EPF, and EIB. For information on data quality and transparency please see our data transparency index.")),
            ui.layout_sidebar(
                ui.sidebar(
                    "Input options",
                    ui.input_checkbox_group(
                        "total_support_regions",
                        "Select Regions",
                        choices={"united_states": "United States", "europe": "Europe"},
                        selected=["united_states", "europe"],
                    ),
                    ui.input_date_range("total_support_date_range", "Select Date Range", start="2022-01-01", end="2024-12-31"),
                    ui.input_switch("total_support_additive", "Show Cumulative View", value=False),
                    position="fixed",
                    min_width="300px",
                    max_width="300px",
                    bg="#f8f8f8",
                ),
                output_widget("support_plot"),  # Simplified output placement
            ),
            height="800px",
        )


class TotalSupportServer:
    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
        self.df = load_time_series_data(TOTAL_SUPPORT_COLUMNS)
        # Create the reactive calculation in init
        self._filtered_data = reactive.Calc(self._compute_filtered_data)
        # Register outputs immediately
        self.register_outputs()

    def _compute_filtered_data(self):
        """Internal method to compute filtered data."""
        selected_cols = [f"{region}_allocated__billion" for region in self.input.total_support_regions()]

        mask = (pd.to_datetime(self.df["month"]) >= pd.to_datetime(self.input.total_support_date_range()[0])) & (
            pd.to_datetime(self.df["month"]) <= pd.to_datetime(self.input.total_support_date_range()[1])
        )
        filtered_df = self.df[mask].copy()

        if not selected_cols:
            return pd.DataFrame()

        result = filtered_df[["month"] + selected_cols]

        if self.input.total_support_additive():
            for col in selected_cols:
                result[col] = result[col].cumsum()

            # Calculate total if both regions are selected
            if len(selected_cols) == 2:
                result["total"] = result[selected_cols].sum(axis=1)

        return result

    def create_plot(self):
        """Create and return the plot figure."""
        data = self._filtered_data()
        if data.empty:
            return go.Figure()

        if self.input.total_support_additive():
            fig = go.Figure()

            # Get the maximum values to determine plotting order
            max_us = data["united_states_allocated__billion"].max() if "united_states_allocated__billion" in data.columns else 0
            max_eu = data["europe_allocated__billion"].max() if "europe_allocated__billion" in data.columns else 0

            # Plot the larger value first (in background)
            regions = sorted(self.input.total_support_regions(), key=lambda x: data[f"{x}_allocated__billion"].max(), reverse=True)

            for region in regions:
                col_name = f"{region}_allocated__billion"
                name = "United States" if region == "united_states" else "Europe"

                fig.add_trace(
                    go.Scatter(
                        x=data["month"],
                        y=data[col_name],
                        name=name,
                        fill="tozeroy",
                        mode="lines",
                        line=dict(color=COLOR_PALETTE[region], width=2),
                        fillcolor=COLOR_PALETTE[region],
                        opacity=0.85 if region == regions[-1] else 0.75,
                        hovertemplate="%{y:.1f}B $<extra></extra>",
                    )
                )

            # Add total line if both regions are selected
            if len(regions) == 2 and "total" in data.columns:
                fig.add_trace(
                    go.Scatter(
                        x=data["month"],
                        y=data["total"],
                        name="Total Support",
                        mode="lines",
                        line=dict(color=COLOR_PALETTE["total"], width=3, dash="solid"),
                        hovertemplate="Total: %{y:.1f}B $<extra></extra>",
                    )
                )

            title = "Cumulative Support Allocation Over Time"

        else:
            fig = go.Figure()

            for region in self.input.total_support_regions():
                col_name = f"{region}_allocated__billion"
                fig.add_trace(
                    go.Bar(
                        x=data["month"], y=data[col_name], name="United States" if region == "united_states" else "Europe", marker_color=COLOR_PALETTE[region]
                    )
                )

            title = "Monthly Support Allocation"

        fig.update_layout(
            title=title,
            xaxis_title="Month",
            yaxis_title="Allocated Support (Billion $)",
            barmode="group",
            template="plotly_white",
            height=600,
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            showlegend=True,
            hovermode="x unified",
            autosize=True,
            yaxis=dict(
                gridcolor="rgba(0,0,0,0.1)",
                zerolinecolor="rgba(0,0,0,0.2)",
            ),
            xaxis=dict(
                gridcolor="rgba(0,0,0,0.1)",
                zerolinecolor="rgba(0,0,0,0.2)",
            ),
            plot_bgcolor="rgba(255,255,255,1)",
            paper_bgcolor="rgba(255,255,255,1)",
        )

        return fig

    def register_outputs(self):
        """Register all outputs for the module."""

        @self.output
        @render_widget
        def support_plot():
            return self.create_plot()
