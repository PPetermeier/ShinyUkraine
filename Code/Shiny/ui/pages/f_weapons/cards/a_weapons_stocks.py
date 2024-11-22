"""Module for visualizing weapons stocks comparisons between Ukraine and Russia.

This module provides components for creating and managing an interactive visualization
that compares Ukrainian weapon stocks (pre-war, current, and projected) with Russian
pre-war levels. It includes both UI components and server-side logic for data
processing and visualization using a dot plot with connecting lines.
"""

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE, LAST_UPDATE, MARGIN
from server.database import load_data_from_table
from server.queries import WEAPON_STOCKS_PREWAR_QUERY, WEAPON_STOCKS_SUPPORT_QUERY
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget


class WeaponsStocksCard:
    """UI components for the weapons stocks comparison visualization card.

    This class handles the user interface elements for displaying the weapons
    stocks comparison visualization.
    """

    @staticmethod
    def ui() -> ui.card:
        """Create the user interface elements for the visualization card.

        Returns:
            ui.card: A Shiny card containing the visualization.
        """
        return ui.card(
            ui.card_header(
                ui.div(
                    {"class": "d-flex justify-content-between align-items-center"},
                    ui.div(
                        {"class": "flex-grow-1"},
                        ui.h3(
                            "Ukrainian Weapon Stocks and Support vs. Pre-war Russian Stocks"
                        ),
                        ui.div(
                            {"class": "card-subtitle text-muted"},
                            "This figure shows the number of items of Ukrainian pre-war stocks and in-kind military aid commitments to Ukraine between January 24, 2022 and August 31, 2024 (from our dataset) in comparison to pre-war Russian and Ukrainian weapon stocks (from the IISS dataset). Heavy weapons are separated in three categories: tanks, howitzers (155mm/152mm), and MLRS. Pre-war stocks of the Russian army are taken from the IISS Military Balance (2022) study.",
                        ),
                    ),
                ),
            ),
            output_widget("weapons_stocks_plot"),
        )


class WeaponsStocksServer:
    """Server logic for the weapons stocks comparison visualization.

    This class handles data processing, filtering, and plot generation for the
    weapons stocks comparison visualization.

    Attributes:
        input: Shiny input object containing user interface values.
        output: Shiny output object for rendering visualizations.
        session: Shiny session object.
    """

    # Define visualization properties
    PLOT_CONFIG: Dict[str, Any] = {
        "min_height": 400,
        "height_per_equipment": 120,
        "marker_sizes": {"russian": 20, "ukrainian": 16},
        "text_size": 12,
        "line_width": 2,
    }

    # Equipment type mapping
    EQUIPMENT_MAPPING: Dict[str, str] = {
        "mlrs": "Multiple Launch Rocket Systems",
        "ifvs": "IFVs",
        "howitzer155mm": "Howitzer (155/152mm)",
        "tanks": "Tanks",
    }

    def __init__(self, input: Any, output: Any, session: Any):
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

    def _get_safe_value(
        self, data: pd.DataFrame, condition: pd.Series, column: str
    ) -> Optional[float]:
        """Safely extract a numeric value from a DataFrame.

        Args:
            data: Source DataFrame.
            condition: Boolean mask for filtering the DataFrame.
            column: Name of the column containing the value.

        Returns:
            Optional[float]: The extracted value or None if invalid.
        """
        filtered_data = data[condition]
        if (
            filtered_data.empty
            or pd.isna(filtered_data[column].iloc[0])
            or not np.isfinite(filtered_data[column].iloc[0])
        ):
            return None
        return float(filtered_data[column].iloc[0])

    def _compute_filtered_data(self) -> pd.DataFrame:
        """Process and filter data for visualization.

        Returns:
            pd.DataFrame: Processed DataFrame containing weapon stocks data.
        """
        prewar_df = load_data_from_table(table_name_or_query=WEAPON_STOCKS_PREWAR_QUERY)
        support_df = load_data_from_table(
            table_name_or_query=WEAPON_STOCKS_SUPPORT_QUERY
        )

        summary = []
        for equipment, display_name in self.EQUIPMENT_MAPPING.items():
            # Get stock values
            russian_stock = self._get_safe_value(
                prewar_df,
                (prewar_df["equipment_type"] == equipment)
                & (prewar_df["country"] == "Russia"),
                "quantity",
            )

            ukr_prewar = self._get_safe_value(
                prewar_df,
                (prewar_df["equipment_type"] == equipment)
                & (prewar_df["country"] == "Ukraine"),
                "quantity",
            )

            delivered = (
                self._get_safe_value(
                    support_df,
                    (support_df["equipment_type"] == equipment)
                    & (support_df["status"] == "delivered"),
                    "quantity",
                )
                or 0.0
            )

            to_deliver = (
                self._get_safe_value(
                    support_df,
                    (support_df["equipment_type"] == equipment)
                    & (support_df["status"] == "to_be_delivered"),
                    "quantity",
                )
                or 0.0
            )

            # Calculate current and projected stocks
            current_stock = (
                float(ukr_prewar) + delivered
                if ukr_prewar is not None
                else delivered
                if delivered > 0
                else None
            )

            projected_stock = (
                current_stock + to_deliver
                if current_stock is not None
                else (delivered + to_deliver)
                if (delivered > 0 or to_deliver > 0)
                else None
            )

            # Skip if any values are non-finite
            if any(
                v is not None and not np.isfinite(v)
                for v in [russian_stock, current_stock, projected_stock]
            ):
                continue

            summary.append(
                {
                    "equipment_type": display_name,
                    "raw_equipment_type": equipment,
                    "russian_stock": russian_stock,
                    "ukr_prewar": ukr_prewar,
                    "current_stock": current_stock,
                    "projected_stock": projected_stock,
                }
            )

        return pd.DataFrame(summary)

    def create_plot(self) -> go.Figure:
        """Generate the weapons stocks comparison visualization plot.

        Returns:
            go.Figure: Plotly figure object containing the dot plot.
        """
        data = self._filtered_data()
        if data.empty:
            return go.Figure()

        fig = self._create_base_plot(data)
        self._add_russian_stocks(fig, data)
        self._add_ukrainian_stocks(fig, data)
        self._update_figure_layout(fig, data)

        return fig

    def _create_base_plot(self, data: pd.DataFrame) -> go.Figure:
        """Create the base plot figure.

        Args:
            data: DataFrame containing weapon stocks data.

        Returns:
            go.Figure: Base Plotly figure.
        """
        return go.Figure()

    def _add_russian_stocks(self, fig: go.Figure, data: pd.DataFrame) -> None:
        """Add Russian stocks to the plot.

        Args:
            fig: Plotly figure to update.
            data: DataFrame containing weapon stocks data.
        """
        valid_russian = data[pd.notna(data["russian_stock"])]
        if valid_russian.empty:
            return

        # Add points
        fig.add_trace(
            go.Scatter(
                x=valid_russian["russian_stock"].astype(float),
                y=valid_russian.index.tolist(),
                mode="markers+text",
                name="Russian Pre-war Stock",
                marker=dict(
                    symbol="diamond",
                    size=self.PLOT_CONFIG["marker_sizes"]["russian"],
                    color=COLOR_PALETTE["weapon_stocks_russia"],
                    line=dict(color="white", width=1),
                ),
                text=valid_russian["russian_stock"].apply(lambda x: f"{int(x):,}"),
                textposition="top center",
                textfont=dict(size=self.PLOT_CONFIG["text_size"]),
                hovertemplate="Russian Pre-war Stock: %{x:,.0f}<extra></extra>",
            )
        )

        # Add reference lines
        for i, row in valid_russian.iterrows():
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

    def _add_ukrainian_stocks(self, fig: go.Figure, data: pd.DataFrame) -> None:
        """Add Ukrainian stocks to the plot.

        Args:
            fig: Plotly figure to update.
            data: DataFrame containing weapon stocks data.
        """
        # Add connecting lines first
        for i, row in data.iterrows():
            self._add_stock_lines(fig, row, i)

        # Process each equipment type's row in sequence
        for i, row in data.iterrows():
            position_counter = 0  # Reset counter for each equipment type

            # Add pre-war stock point if exists
            if pd.notna(row["ukr_prewar"]):
                self._add_single_point(
                    fig,
                    x=float(row["ukr_prewar"]),
                    y=i,
                    value=int(row["ukr_prewar"]),
                    name="Ukrainian Pre-war Stock",
                    color=COLOR_PALETTE["weapon_stocks_prewar"],
                    position="top center"
                    if position_counter % 2 == 0
                    else "bottom center",
                )
                position_counter += 1

            # Add current stock point if exists
            if pd.notna(row["current_stock"]):
                self._add_single_point(
                    fig,
                    x=float(row["current_stock"]),
                    y=i,
                    value=int(row["current_stock"]),
                    name="Ukrainian Current Stock (with Delivered)",
                    color=COLOR_PALETTE["weapon_stocks_delivered"],
                    position="top center"
                    if position_counter % 2 == 0
                    else "bottom center",
                )
                position_counter += 1

            # Add projected stock point if exists
            if pd.notna(row["projected_stock"]):
                self._add_single_point(
                    fig,
                    x=float(row["projected_stock"]),
                    y=i,
                    value=int(row["projected_stock"]),
                    name="Ukrainian Projected Stock (with Committed)",
                    color=COLOR_PALETTE["weapon_stocks_pending"],
                    position="top center"
                    if position_counter % 2 == 0
                    else "bottom center",
                )
                position_counter += 1

    def _add_single_point(
        self,
        fig: go.Figure,
        x: float,
        y: int,
        value: int,
        name: str,
        color: str,
        position: str,
    ) -> None:
        """Add a single point with text to the plot.

        Args:
            fig: Plotly figure to update.
            x: X-coordinate for the point
            y: Y-coordinate for the point
            value: Value to display as text
            name: Name for the legend
            color: Color for the point
            position: Text position ('top center' or 'bottom center')
        """
        fig.add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                mode="markers+text",
                name=name,
                marker=dict(
                    symbol="circle",
                    size=self.PLOT_CONFIG["marker_sizes"]["ukrainian"],
                    color=color,
                    line=dict(color="white", width=1),
                ),
                text=[f"{value:,}"],
                textposition=[position],
                textfont=dict(size=self.PLOT_CONFIG["text_size"]),
                hovertemplate=f"{name}: %{{x:,.0f}}<extra></extra>",
                showlegend=y == 0,  # Only show in legend for first row
            )
        )

    def _add_stock_lines(self, fig: go.Figure, row: pd.Series, index: int) -> None:
        """Add connecting lines between stock points.

        Args:
            fig: Plotly figure to update.
            row: Data row containing stock values.
            index: Y-axis position index.
        """
        # Pre-war to current line
        if pd.notna(row["ukr_prewar"]) and pd.notna(row["current_stock"]):
            fig.add_trace(
                go.Scatter(
                    x=[float(row["ukr_prewar"]), float(row["current_stock"])],
                    y=[index, index],
                    mode="lines",
                    line=dict(
                        color=COLOR_PALETTE["weapon_stocks_delivered"],
                        width=self.PLOT_CONFIG["line_width"],
                    ),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

        # Current to projected line
        if pd.notna(row["current_stock"]) and pd.notna(row["projected_stock"]):
            fig.add_trace(
                go.Scatter(
                    x=[float(row["current_stock"]), float(row["projected_stock"])],
                    y=[index, index],
                    mode="lines",
                    line=dict(
                        color=COLOR_PALETTE["weapon_stocks_pending"],
                        width=self.PLOT_CONFIG["line_width"],
                    ),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

    def _add_stock_points(
        self, fig: go.Figure, data: pd.DataFrame, column: str, name: str, color: str
    ) -> None:
        """Add stock points to the plot with alternating above/below text positions.

        Args:
            fig: Plotly figure to update.
            data: DataFrame containing weapon stocks data.
            column: Name of the column containing stock values.
            name: Name for the legend.
            color: Color for the points.
        """
        valid_data = data[pd.notna(data[column])]
        if not valid_data.empty:
            text_values = []
            text_positions = []

            for idx, row in valid_data.iterrows():
                value = int(row[column])
                text_values.append(f"{value:,}")

                # Simple alternating pattern between top and bottom
                if idx % 2 == 0:
                    text_positions.append("top center")
                else:
                    text_positions.append("bottom center")

            fig.add_trace(
                go.Scatter(
                    x=valid_data[column].astype(float),
                    y=valid_data.index.tolist(),
                    mode="markers+text",
                    name=name,
                    marker=dict(
                        symbol="circle",
                        size=self.PLOT_CONFIG["marker_sizes"]["ukrainian"],
                        color=color,
                        line=dict(color="white", width=1),
                    ),
                    text=text_values,
                    textposition=text_positions,
                    textfont=dict(size=self.PLOT_CONFIG["text_size"]),
                    hovertemplate=f"{name}: %{{x:,.0f}}<extra></extra>",
                )
            )

    def _update_figure_layout(self, fig: go.Figure, data: pd.DataFrame) -> None:
        """Update the layout of the figure.

        Args:
            fig: Plotly figure to update.
            data: DataFrame containing weapon stocks data.
        """
        equipment_types = data["equipment_type"].unique()
        plot_height = max(
            self.PLOT_CONFIG["min_height"],
            len(equipment_types) * self.PLOT_CONFIG["height_per_equipment"],
        )

        fig.update_layout(
            title=dict(
                text=f"Weapon Stocks Comparison<br>"
                f"<sub>Last updated: {LAST_UPDATE}, Sheet: Fig 12</sub>",
                font=dict(size=14),
                y=0.95,
                x=0.5,
                xanchor="center",
                yanchor="top",
            ),
            height=plot_height,
            margin=MARGIN,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.02,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.2)",
                borderwidth=1,
            ),
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
                tickvals=list(range(len(equipment_types))),
                showgrid=False,
            ),
            plot_bgcolor="rgba(255,255,255,1)",
            paper_bgcolor="rgba(255,255,255,1)",
        )

    def register_outputs(self) -> None:
        """Register the plot output with Shiny."""

        @self.output
        @render_widget
        def weapons_stocks_plot() -> go.Figure:
            return self.create_plot()
