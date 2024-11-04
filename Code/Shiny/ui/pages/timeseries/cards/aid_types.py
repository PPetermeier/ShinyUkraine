"""
Aid types visualization card.
"""

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE
from server.database import load_time_series_data, AID_TYPES_COLUMNS
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget


class AidTypesCard:
    """UI components for the aid types visualization card."""

    @staticmethod
    def ui():
        """Return the card UI elements."""
        return ui.card(
            ui.card_header(ui.h3("Aid Types Over Time"), ui.div({"class": "card-subtitle text-muted"}, "Monthly and cumulative aid allocation by type")),
            ui.layout_sidebar(
                ui.sidebar(
                    "Input options",
                    ui.input_checkbox_group(
                        "aid_types_select",
                        "Select Aid Types",
                        choices={"military": "Military Aid", "financial": "Financial Aid", "humanitarian": "Humanitarian Aid"},
                        selected=["military", "financial", "humanitarian"],
                    ),
                    ui.input_date_range("aid_types_date_range", "Select Date Range", start="2022-01-01", end="2024-12-31"),
                    ui.input_switch("aid_types_exclude_us", "Exclude US Data", value=False),
                    ui.input_switch("aid_types_cumulative", "Show Cumulative View", value=False),
                    position="fixed",
                    min_width="300px",
                    max_width="300px",
                    bg="#f8f8f8",
                ),
                output_widget("aid_types_plot"),
            ),
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

    def _get_column_name(self, aid_type, exclude_us=False):
        """Helper method to get the correct column name based on aid type and US exclusion."""
        if aid_type == "humanitarian":
            # Humanitarian aid is always without US
            return "humanitarian_aid_allocated__billion"
        elif aid_type == "financial":
            return "financial_aid_allocated__billion_without_us" if exclude_us else "financial_aid_allocated__billion"
        else:  # military
            return "military_aid_allocated__billion_without_us" if exclude_us else "military_aid_allocated__billion"

    def _compute_filtered_data(self):
        """Internal method to compute filtered data based on user inputs."""
        # Filter date range
        mask = (pd.to_datetime(self.df["month"]) >= pd.to_datetime(self.input.aid_types_date_range()[0])) & (
            pd.to_datetime(self.df["month"]) <= pd.to_datetime(self.input.aid_types_date_range()[1])
        )
        filtered_df = self.df[mask].copy()

        # Select relevant columns based on aid types and US exclusion
        selected_cols = []
        for aid_type in self.input.aid_types_select():
            col_name = self._get_column_name(aid_type, self.input.aid_types_exclude_us())
            if col_name in self.df.columns:
                selected_cols.append(col_name)

        if not selected_cols:
            return pd.DataFrame()

        result = filtered_df[["month"] + selected_cols]

        # Calculate cumulative sums if needed
        if self.input.aid_types_cumulative():
            for col in selected_cols:
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
            "military_aid_allocated__billion_without_us": "Military Aid (Excl. US)",
            "financial_aid_allocated__billion": "Financial Aid",
            "financial_aid_allocated__billion_without_us": "Financial Aid (Excl. US)",
            "humanitarian_aid_allocated__billion": "Humanitarian Aid",
        }

        if self.input.aid_types_cumulative():
            # Create stacked area chart for cumulative view
            for col in data.columns:
                if col != "month":
                    aid_type = "military" if "military" in col else "financial" if "financial" in col else "humanitarian"
                    fig.add_trace(
                        go.Scatter(
                            x=data["month"],
                            y=data[col],
                            name=name_mapping.get(col, col),
                            stackgroup="one",
                            mode="lines",
                            line=dict(width=0),
                            fillcolor=COLOR_PALETTE[aid_type],
                            opacity=0.8,
                            hovertemplate="%{y:.1f}B €<extra></extra>",
                        )
                    )

        else:
            # Create stacked bar chart for monthly view
            for col in data.columns:
                if col != "month":
                    aid_type = "military" if "military" in col else "financial" if "financial" in col else "humanitarian"
                    fig.add_trace(
                        go.Bar(
                            x=data["month"],
                            y=data[col],
                            name=name_mapping.get(col, col),
                            marker_color=COLOR_PALETTE[aid_type],
                            opacity=0.8,
                            hovertemplate="%{y:.1f}B €<extra></extra>",
                        )
                    )

        view_type = "Cumulative" if self.input.aid_types_cumulative() else "Monthly"
        data_scope = "Excluding US" if self.input.aid_types_exclude_us() else "Including US"

        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Allocated Support (Billion €)",
            template="plotly_white",
            height=600,
            margin=dict(l=20, r=20, t=20, b=20),  # Reduced top margin since title is in card header
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
            barmode="stack" if not self.input.aid_types_cumulative() else None,
        )

        return fig

    def register_outputs(self):
        """Register all outputs for the module."""

        @self.output
        @render_widget
        def aid_types_plot():
            return self.create_plot()
