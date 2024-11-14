"""
Aid types visualization card.
"""

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE, LAST_UPDATE, MARGIN
from server.database import AID_TYPES_COLUMNS, load_time_series_data
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget
from ....colorutilities import desaturate_color


class AidTypesCard:
    """UI components for the aid types visualization card."""

    @staticmethod
    def ui():
        """Return the card UI elements."""
        return ui.card(
            ui.card_header(
                ui.h3("Monthly and cumulative bilateral aid allocation by type"),
                ui.div(
                    {"class": "d-flex flex-row justify-content-between"},  # Changed to flex-row and justify-content-between
                    ui.div(
                        {"class": "flex-grow-1 me-4"},  # Added margin-end to create space before toggle
                        "Includes bilateral allocations to Ukraine. Allocations are defined as aid which has been "
                        "delivered or specified for delivery. Does not include private donations, support for refugees "
                        "outside of Ukraine, and aid by international organizations. Data on European Union aid include "
                        "the EU Commission and Council, EPF, and EIB. For information on data quality and transparency "
                        "please see our data transparency index.",
                    ),
                    ui.div(
                        {"class": "flex-shrink-0 d-flex align-items-center"},  # Made toggle container non-shrinkable
                        ui.span({"class": "me-2"}, "Cumulative"),  # Added explicit spacing
                        ui.input_switch("aid_types_cumulative", None, value=False),
                    ),
                ),
            ),
            output_widget("aid_types_plot"),
            height="800px",
        )


class AidTypesServer:
    """Server logic for the aid types visualization card."""

    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
        self.df = load_time_series_data(AID_TYPES_COLUMNS)
        self._filtered_data = reactive.Calc(self._compute_filtered_data)
        self.register_outputs()

    def _compute_filtered_data(self):
        """Internal method to compute filtered data."""
        # Use all aid types and include US data by default
        result = self.df.copy()
        
        # Select all aid types columns
        aid_columns = ["military_aid_allocated__billion", 
                      "financial_aid_allocated__billion",
                      "humanitarian_aid_allocated__billion"]

        result = result[["month"] + aid_columns]

        # Calculate cumulative sums if needed
        if self.input.aid_types_cumulative():
            for col in aid_columns:
                result[col] = result[col].cumsum()

        return result


    def create_plot(self):
        """Create and return the plot figure."""
        data = self._filtered_data()
        if data.empty:
            return go.Figure()

        fig = go.Figure()

        # Define consistent naming for the legend
        name_mapping = {
            "military_aid_allocated__billion": "Military Aid",
            "financial_aid_allocated__billion": "Financial Aid",
            "humanitarian_aid_allocated__billion": "Humanitarian Aid",
        }

        # Set the title based on the view type
        plot_title = "Cumulative Support Allocation Over Time" if self.input.aid_types_cumulative() else "Monthly Support Allocation"

        if self.input.aid_types_cumulative():
            # Your existing cumulative view code...
            data_cols = [col for col in data.columns if col != "month"]
            sorted_cols = sorted(data_cols, key=lambda x: data[x].max())

            for i, col in enumerate(sorted_cols):
                aid_type = "military" if "military" in col else "financial" if "financial" in col else "humanitarian"
                fig.add_trace(
                    go.Scatter(
                        x=data["month"],
                        y=data[col],
                        name=name_mapping.get(col, col),
                        stackgroup="one",
                        mode="lines",
                        line=dict(
                            color=COLOR_PALETTE[aid_type],
                            width=2
                        ),
                        fill='tonexty' if i > 0 else 'tozeroy',
                        fillcolor=desaturate_color(COLOR_PALETTE[aid_type], factor=0.6),
                        hovertemplate="%{y:.1f}B €<extra></extra>",
                    )
                )
        else:
            # Your existing monthly view code...
            for col in data.columns:
                if col != "month":
                    aid_type = "military" if "military" in col else "financial" if "financial" in col else "humanitarian"
                    fig.add_trace(
                        go.Bar(
                            x=data["month"],
                            y=data[col],
                            name=name_mapping.get(col, col),
                            marker_color=COLOR_PALETTE[aid_type],
                            hovertemplate="%{y:.1f}B €<extra></extra>",
                        )
                    )


        fig.update_layout(
            title= dict(
        text=f"{plot_title}<br><sub>Last updated: {LAST_UPDATE}, Sheet: Fig 6</sub>",
        font=dict(size=14),
        y=0.95,
        x=0.5,
        xanchor='center',
        yanchor='top'
    ),  # Using the title we defined above
            xaxis_title="Month",
            yaxis_title="Billion €",
            template="plotly_white",
            height=600,
            margin=MARGIN,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.2)",
                borderwidth=1,
                itemsizing="constant",
                tracegroupgap=5
            ),
            showlegend=True,
            hovermode="x unified",
            autosize=True,
            width=None,
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
            barmode="stack" if not self.input.aid_types_cumulative() else None,
        )

        return fig

    def register_outputs(self):
        """Register all outputs for the module."""

        @self.output
        @render_widget
        def aid_types_plot():
            return self.create_plot()