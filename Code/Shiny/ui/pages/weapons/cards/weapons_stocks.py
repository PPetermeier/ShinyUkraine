"""
Weapons stocks comparison visualization card with dot plot visualization.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE, LAST_UPDATE, MARGIN
from server.database import load_data_from_table
from server.queries import WEAPON_STOCKS_SUPPORT_QUERY, WEAPON_STOCKS_PREWAR_QUERY
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget


class WeaponsStocksCard:
    """UI components for the weapons stocks comparison visualization card."""

    @staticmethod
    def ui():
        return ui.card(
            ui.card_header(
                ui.div(
                    {"class": "d-flex justify-content-between align-items-center"},
                    ui.div(
                        {"class": "flex-grow-1"},
                        ui.h3("Ukrainian Weapon Stocks and Support vs. Pre-war Russian Stocks"),
                        ui.div(
                            {"class": "card-subtitle text-muted"},
                            "Evolution of Ukrainian weapon stocks through Western support compared to Russian pre-war levels.",
                        ),
                    ),
                ),
            ),
            output_widget("weapons_stocks_plot"),
            # Remove fixed height to allow dynamic sizing
        )


class WeaponsStocksServer:
    """Server logic for the weapons stocks comparison visualization card."""

    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
        self._filtered_data = reactive.Calc(self._compute_filtered_data)

    def _compute_filtered_data(self):
        """Process data for visualization."""
        # Get pre-war stocks
        prewar_df = load_data_from_table(table_name_or_query=WEAPON_STOCKS_PREWAR_QUERY)

        # Get support data
        support_df = load_data_from_table(table_name_or_query=WEAPON_STOCKS_SUPPORT_QUERY)

        # This also controls the ordering of the plot
        equipment_name_mapping = {"mlrs": "Multiple Launch Rocket Systems", "ifvs": "IFVs", "howitzer155mm": "Howitzer (155/152mm)", "tanks": "Tanks"}

        summary = []
        for equipment in equipment_name_mapping.keys():
            # Get Russian pre-war stock
            russian_data = prewar_df[(prewar_df["equipment_type"] == equipment) & (prewar_df["country"] == "Russia")]
            russian_stock = (
                russian_data["quantity"].iloc[0]
                if not russian_data.empty and pd.notna(russian_data["quantity"].iloc[0]) and np.isfinite(russian_data["quantity"].iloc[0])
                else None
            )

            # Get Ukrainian pre-war stock
            ukr_prewar_data = prewar_df[(prewar_df["equipment_type"] == equipment) & (prewar_df["country"] == "Ukraine")]
            ukr_prewar = (
                ukr_prewar_data["quantity"].iloc[0]
                if not ukr_prewar_data.empty and pd.notna(ukr_prewar_data["quantity"].iloc[0]) and np.isfinite(ukr_prewar_data["quantity"].iloc[0])
                else None
            )

            # Get delivered support with safe conversion to float
            delivered_data = support_df[(support_df["equipment_type"] == equipment) & (support_df["status"] == "delivered")]
            delivered = (
                float(delivered_data["quantity"].iloc[0])
                if not delivered_data.empty and pd.notna(delivered_data["quantity"].iloc[0]) and np.isfinite(delivered_data["quantity"].iloc[0])
                else 0.0
            )

            # Get to-be-delivered support with safe conversion to float
            to_deliver_data = support_df[(support_df["equipment_type"] == equipment) & (support_df["status"] == "to_be_delivered")]
            to_deliver = (
                float(to_deliver_data["quantity"].iloc[0])
                if not to_deliver_data.empty and pd.notna(to_deliver_data["quantity"].iloc[0]) and np.isfinite(to_deliver_data["quantity"].iloc[0])
                else 0.0
            )

            # Calculate current and projected stocks only if pre-war stock exists
            if ukr_prewar is not None:
                current_stock = float(ukr_prewar) + delivered
                projected_stock = current_stock + to_deliver
            else:
                current_stock = delivered if delivered > 0 else None
                projected_stock = (delivered + to_deliver) if (delivered > 0 or to_deliver > 0) else None

            # Ensure all values are finite
            if (
                (russian_stock is not None and not np.isfinite(russian_stock))
                or (current_stock is not None and not np.isfinite(current_stock))
                or (projected_stock is not None and not np.isfinite(projected_stock))
            ):
                continue

            summary.append(
                {
                    "equipment_type": equipment_name_mapping.get(equipment, equipment.upper()),
                    "raw_equipment_type": equipment,
                    "russian_stock": russian_stock,
                    "ukr_prewar": ukr_prewar,
                    "current_stock": current_stock,
                    "projected_stock": projected_stock,
                }
            )

        return pd.DataFrame(summary)

    def create_plot(self):
        """Create the dot plot visualization."""
        data = self._filtered_data()

        if data.empty:
            return go.Figure()

        fig = go.Figure()

        # Calculate y-positions for each equipment type
        equipment_types = data["equipment_type"].unique()
        y_positions = list(range(len(equipment_types)))

        # Add Russian stock markers (only for valid values)
        valid_russian = data[pd.notna(data["russian_stock"])]
        if not valid_russian.empty:
            fig.add_trace(
                go.Scatter(
                    x=valid_russian["russian_stock"].astype(float),
                    y=valid_russian.index.tolist(),
                    mode="markers",
                    name="Russian Pre-war Stock",
                    marker=dict(symbol="diamond", size=20, color=COLOR_PALETTE["weapon_stocks_russia"], line=dict(color="white", width=1)),
                    hovertemplate="Russian Pre-war Stock: %{x:,.0f}<extra></extra>",
                )
            )

            # Add vertical reference lines only for valid Russian stocks
            for i, row in valid_russian.iterrows():
                if pd.notna(row["russian_stock"]):
                    fig.add_shape(
                        type="line",
                        x0=0,
                        x1=float(row["russian_stock"]),
                        y0=i,
                        y1=i,
                        line=dict(
                            color=COLOR_PALETTE["weapon_stocks_russia"],
                            width=1,
                            dash="dot",
                        ),
                    )

        # Add Ukrainian data points and lines only where values exist
        for i, row in data.iterrows():
            # Pre-war to current line
            if pd.notna(row["ukr_prewar"]) and pd.notna(row["current_stock"]):
                fig.add_trace(
                    go.Scatter(
                        x=[float(row["ukr_prewar"]), float(row["current_stock"])],
                        y=[i, i],
                        mode="lines",
                        line=dict(color=COLOR_PALETTE["weapon_stocks_delivered"], width=2),
                        showlegend=False,
                        hoverinfo="skip",
                    )
                )

            # Current to projected line
            if pd.notna(row["current_stock"]) and pd.notna(row["projected_stock"]):
                fig.add_trace(
                    go.Scatter(
                        x=[float(row["current_stock"]), float(row["projected_stock"])],
                        y=[i, i],
                        mode="lines",
                        line=dict(color=COLOR_PALETTE["weapon_stocks_pending"], width=2),
                        showlegend=False,
                        hoverinfo="skip",
                    )
                )

        # Add Ukrainian pre-war points
        valid_prewar = data[pd.notna(data["ukr_prewar"])]
        if not valid_prewar.empty:
            fig.add_trace(
                go.Scatter(
                    x=valid_prewar["ukr_prewar"].astype(float),
                    y=valid_prewar.index.tolist(),
                    mode="markers",
                    name="Ukrainian Pre-war Stock",
                    marker=dict(symbol="circle", size=16, color=COLOR_PALETTE["weapon_stocks_prewar"], line=dict(color="white", width=1)),
                    hovertemplate="Ukrainian Pre-war Stock: %{x:,.0f}<extra></extra>",
                )
            )

        # Add current stock points
        valid_current = data[pd.notna(data["current_stock"])]
        if not valid_current.empty:
            fig.add_trace(
                go.Scatter(
                    x=valid_current["current_stock"].astype(float),
                    y=valid_current.index.tolist(),
                    mode="markers",
                    name="Ukrainian Current Stock (with Delivered)",
                    marker=dict(symbol="circle", size=16, color=COLOR_PALETTE["weapon_stocks_delivered"], line=dict(color="white", width=1)),
                    hovertemplate="Current Stock: %{x:,.0f}<extra></extra>",
                )
            )

        # Add projected stock points
        valid_projected = data[pd.notna(data["projected_stock"])]
        if not valid_projected.empty:
            fig.add_trace(
                go.Scatter(
                    x=valid_projected["projected_stock"].astype(float),
                    y=valid_projected.index.tolist(),
                    mode="markers",
                    name="Ukrainian Projected Stock (with Committed)",
                    marker=dict(symbol="circle", size=16, color=COLOR_PALETTE["weapon_stocks_pending"], line=dict(color="white", width=1)),
                    hovertemplate="Projected Stock: %{x:,.0f}<extra></extra>",
                )
            )

        # Calculate dynamic height based on number of equipment types
        plot_height = max(400, len(equipment_types) * 100)

        # Update layout
        fig.update_layout(
            title=dict(
                text=f"Weapon Stocks Comparison<br><sub>Last updated: {LAST_UPDATE}</sub>", font=dict(size=14), y=0.95, x=0.5, xanchor="center", yanchor="top"
            ),
            height=plot_height,
            margin=MARGIN,
            showlegend=True,
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.02, bgcolor="rgba(255, 255, 255, 0.8)", bordercolor="rgba(0, 0, 0, 0.2)", borderwidth=1),
            hovermode="closest",
            xaxis=dict(
                title="Number of Units",
                showgrid=False,
                gridcolor="rgba(0,0,0,0.1)",
                zeroline=True,
                zerolinecolor="rgba(0,0,0,0.2)",
            ),
            yaxis=dict(
                ticktext=list(equipment_types),
                tickvals=y_positions,
                showgrid=False,
            ),
            plot_bgcolor="rgba(255,255,255,1)",
            paper_bgcolor="rgba(255,255,255,1)",
        )

        return fig

    def register_outputs(self):
        """Register all outputs for the module."""

        @self.output
        @render_widget
        def weapons_stocks_plot():
            return self.create_plot()
