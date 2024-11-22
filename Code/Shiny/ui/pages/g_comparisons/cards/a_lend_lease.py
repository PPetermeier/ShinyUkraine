"""Module for visualizing historical military support comparisons.

This module provides components for creating and managing an interactive visualization
that compares military equipment support across major historical conflicts, including
WW2 Lend-Lease and current support for Ukraine. It shows both delivered and planned
equipment transfers across different categories (heavy equipment, artillery, air).
"""

from typing import Any, Dict, List, Tuple
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from shiny import ui
from shinywidgets import output_widget, render_widget

from ....colorutilities import desaturate_color
from config import COLOR_PALETTE, LAST_UPDATE
from server import WW2_CONFLICTS, WW2_EQUIPMENT_CATEGORIZED_QUERY, load_data_from_table


class WW2EquipmentComparisonCard:
    """UI components for the WW2 equipment comparison visualization card.

    This class handles the user interface elements for displaying the historical
    military support comparison visualization, including controls for switching
    between absolute and relative views.
    """

    @staticmethod
    def ui() -> ui.card:
        """Create the user interface elements for the visualization card.

        Returns:
            ui.card: A Shiny card containing the visualization and controls.
        """
        return ui.card(
            ui.card_header(
                ui.div(
                    {"class": "d-flex justify-content-between align-items-center"},
                    ui.div(
                        {"class": "flex-grow-1"},
                        ui.h3("Historical Military Support Comparison"),
                        ui.div(
                            {"class": "card-subtitle text-muted"},
                            "This figure compares the number of weapons sent by foreign powers during WW2 and during the Spanish Civil War (green bars) to the number of weapons committed to Ukraine thus far. Historical data on weapon support for the US Lend-Lease program of WW2 comes from the US Department of State (1945) and US Department of War (1946). For the Spanish Civil War we use data from Alpert (2013) and Rybalkin (2000). Weapon support to Ukraine is from our database. See Working Paper for relevant citations.",
                        ),
                    ),
                    ui.div({"class": "ms-3"}, ui.input_switch("show_absolute", "Show Absolute Numbers", value=False)),
                ),
            ),
            output_widget("equipment_comparison_plot"),
        )


class WW2EquipmentComparisonServer:
    """Server logic for the WW2 equipment comparison visualization.

    This class handles data processing, filtering, and plot generation for the
    historical military support comparison visualization.

    Attributes:
        input: Shiny input object containing user interface values.
        output: Shiny output object for rendering visualizations.
        session: Shiny session object.
    """

    # Define visualization properties
    PLOT_CONFIG: Dict[str, Any] = {
        "height": 700,
        "margin": dict(t=180, l=50, r=50, b=50),
        "subplot_titles": {"heavy": "Heavy Equipment (Tanks)", "artillery": "Artillery Systems", "air": "Combat Aircraft"},
        "subplot_positions": {"heavy": (0.16, 1), "artillery": (0.5, 2), "air": (0.84, 3)},
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

    def _compute_filtered_data(self) -> pd.DataFrame:
        """Process and filter data based on user selections.

        Returns:
            pd.DataFrame: Processed DataFrame containing equipment comparison data.
        """
        conflicts_str = ", ".join(f"'{conflict}'" for conflict in WW2_CONFLICTS)
        query = WW2_EQUIPMENT_CATEGORIZED_QUERY.format(conflicts=conflicts_str)
        df = load_data_from_table(table_name_or_query=query)

        if not self.input.show_absolute():
            self._normalize_data(df)

        return df

    def _normalize_data(self, df: pd.DataFrame) -> None:
        """Normalize data values by category.

        Args:
            df: DataFrame to normalize (modified in-place).
        """
        for category in df["category"].unique():
            mask = df["category"] == category
            max_delivered = df.loc[mask, "delivered"].max()
            if max_delivered > 0:
                df.loc[mask, "delivered_pct"] = df.loc[mask, "delivered"] / max_delivered * 100
                df.loc[mask, "to_be_delivered_pct"] = df.loc[mask, "to_be_delivered"] / max_delivered * 100

    def create_plot(self) -> go.Figure:
        """Generate the equipment comparison visualization plot.

        Returns:
            go.Figure: Plotly figure object containing the subplot comparison.
        """
        data = self._compute_filtered_data()
        if data.empty:
            return go.Figure()

        fig = self._create_subplot_figure()
        self._add_category_plots(fig, data)
        self._update_figure_layout(fig)

        return fig

    def _create_subplot_figure(self) -> go.Figure:
        """Create the base subplot figure.

        Returns:
            go.Figure: Base Plotly figure with subplots.
        """
        return make_subplots(rows=1, cols=3, horizontal_spacing=0.05)

    def _get_value_formatting(self) -> Dict[str, str]:
        """Get formatting configuration based on view type.

        Returns:
            Dict[str, str]: Dictionary containing formatting strings.
        """
        if self.input.show_absolute():
            return {"suffix": " units", "number_format": ":,d", "value_format": "{:,d}"}
        return {"suffix": "%", "number_format": ":.1f", "value_format": "{:.1f}"}

    def _add_category_plots(self, fig: go.Figure, data: pd.DataFrame) -> None:
        """Add category-specific plots to the figure.

        Args:
            fig: Plotly figure to update.
            data: DataFrame containing the visualization data.
        """
        formatting = self._get_value_formatting()

        for category, (_, col) in self.PLOT_CONFIG["subplot_positions"].items():
            category_data = self._prepare_category_data(data, category)

            if not category_data.empty:
                self._add_category_traces(fig=fig, category_data=category_data, col=col, formatting=formatting)

    def _prepare_category_data(self, data: pd.DataFrame, category: str) -> pd.DataFrame:
        """Prepare data for a specific category.

        Args:
            data: Source DataFrame.
            category: Category to filter for.

        Returns:
            pd.DataFrame: Filtered and sorted DataFrame.
        """
        category_data = data[data["category"] == category].copy()
        if not category_data.empty:
            category_data["total"] = category_data["delivered"] + category_data["to_be_delivered"]
            return category_data.sort_values("total", ascending=True)
        return category_data

    def _add_category_traces(self, fig: go.Figure, category_data: pd.DataFrame, col: int, formatting: Dict[str, str]) -> None:
        """Add traces for a specific category to the figure.

        Args:
            fig: Plotly figure to update.
            category_data: DataFrame containing category-specific data.
            col: Column number for the subplot.
            formatting: Dictionary containing formatting strings.
        """
        for conflict in category_data["military_conflict"].unique():
            conflict_data = category_data[category_data["military_conflict"] == conflict]

            values = self._get_trace_values(conflict_data, formatting)

            # Add delivered amounts
            fig.add_trace(self._create_delivered_trace(conflict=conflict, values=values, formatting=formatting, show_legend=(col == 1)), row=1, col=col)

            # Add to-be-delivered amounts if they exist
            if conflict_data["to_be_delivered"].iloc[0] > 0:
                fig.add_trace(self._create_planned_trace(conflict=conflict, values=values, formatting=formatting), row=1, col=col)

    def _get_trace_values(self, conflict_data: pd.DataFrame, formatting: Dict[str, str]) -> Dict[str, Any]:
        """Get values for creating traces.

        Args:
            conflict_data: DataFrame containing conflict-specific data.
            formatting: Dictionary containing formatting strings.

        Returns:
            Dict[str, Any]: Dictionary containing trace values.
        """
        if self.input.show_absolute():
            return {"delivered": conflict_data["delivered"].astype(int), "to_deliver": conflict_data["to_be_delivered"].astype(int)}
        return {"delivered": conflict_data["delivered_pct"], "to_deliver": conflict_data["to_be_delivered_pct"]}

    def _create_delivered_trace(self, conflict: str, values: Dict[str, Any], formatting: Dict[str, str], show_legend: bool) -> go.Bar:
        """Create a trace for delivered equipment.

        Args:
            conflict: Name of the conflict.
            values: Dictionary containing trace values.
            formatting: Dictionary containing formatting strings.
            show_legend: Whether to show this trace in the legend.

        Returns:
            go.Bar: Configured bar trace for delivered equipment.
        """
        return go.Bar(
            name=conflict,
            y=[conflict],
            x=values["delivered"],
            orientation="h",
            marker_color=COLOR_PALETTE[conflict],
            legendgroup=conflict,
            showlegend=show_legend,
            customdata=[[d, t] for d, t in zip(values["delivered"], values["to_deliver"])],
            hovertemplate=(
                f"%{{y}}<br>"
                f"Delivered: %{{customdata[0]{formatting['number_format']}}}{formatting['suffix']}<br>"
                f"To be delivered: %{{customdata[1]{formatting['number_format']}}}{formatting['suffix']}"
            ),
            text=[f"{formatting['value_format'].format(v)}{formatting['suffix']}" if v > 0 else "" for v in values["delivered"]],
            textposition="inside",
            textfont=dict(color="white"),
            insidetextanchor="middle",
        )

    def _create_planned_trace(self, conflict: str, values: Dict[str, Any], formatting: Dict[str, str]) -> go.Bar:
        """Create a trace for planned equipment deliveries.

        Args:
            conflict: Name of the conflict.
            values: Dictionary containing trace values.
            formatting: Dictionary containing formatting strings.

        Returns:
            go.Bar: Configured bar trace for planned deliveries.
        """
        return go.Bar(
            name=f"{conflict} (Planned)",
            y=[conflict],
            x=values["to_deliver"],
            orientation="h",
            marker_color=desaturate_color(COLOR_PALETTE[conflict]),
            legendgroup=conflict,
            showlegend=False,
            base=values["delivered"],
            customdata=[[t] for t in values["to_deliver"]],
            hovertemplate=(f"%{{y}}<br>" f"Additional to be delivered: %{{customdata[0]{formatting['number_format']}}}" f"{formatting['suffix']}"),
            text=[f"{formatting['value_format'].format(v)}{formatting['suffix']}" if v > 0 else "" for v in values["to_deliver"]],
            textposition="inside",
            textfont=dict(color="white"),
            insidetextanchor="middle",
        )

    def _update_figure_layout(self, fig: go.Figure) -> None:
        """Update the layout of the figure.

        Args:
            fig: Plotly figure to update.
        """
        fig.update_layout(
            height=self.PLOT_CONFIG["height"],
            margin=self.PLOT_CONFIG["margin"],
            barmode="stack",
            template="plotly_white",
            title=self._create_title_dict(),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.12,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.2)",
                borderwidth=1,
            ),
            showlegend=True,
            hovermode="y unified",
            annotations=self._create_subplot_annotations(),
        )

        self._update_subplot_axes(fig)

    def _create_title_dict(self) -> Dict[str, Any]:
        """Create the title configuration dictionary.

        Returns:
            Dict[str, Any]: Title configuration dictionary.
        """
        return dict(
            text=(
                "Historical Military Support Comparison<br>"
                "<span style='font-size: 12px; color: gray;'>"
                "This figure compares the scale of military equipment support across "
                "major historical conflicts. Data shows both delivered and planned "
                f"equipment transfers.<br>Last updated: {LAST_UPDATE}, Sheet: Fig 15</span>"
            ),
            x=0.5,
            y=0.98,
            xanchor="center",
            yanchor="top",
            font=dict(size=16),
        )

    def _create_subplot_annotations(self) -> List[Dict[str, Any]]:
        """Create annotations for subplot titles.

        Returns:
            List[Dict[str, Any]]: List of annotation configurations.
        """
        return [
            dict(text=title, x=x_pos, y=1.08, showarrow=False, xref="paper", yref="paper", font=dict(size=14, weight="bold"))
            for (title, (x_pos, _)) in zip(self.PLOT_CONFIG["subplot_titles"].values(), self.PLOT_CONFIG["subplot_positions"].values())
        ]

    def _update_subplot_axes(self, fig: go.Figure) -> None:
        """Update the axes for all subplots.

        Args:
            fig: Plotly figure to update.
        """
        for i in range(1, 4):
            fig.update_xaxes(showgrid=True, gridcolor="rgba(0,0,0,0.1)", zeroline=True, zerolinecolor="rgba(0,0,0,0.2)", row=1, col=i, showticklabels=False)
            fig.update_yaxes(showgrid=False, title="", showticklabels=False, row=1, col=i)

    def register_outputs(self) -> None:
        """Register the plot output with Shiny."""

        @self.output
        @render_widget
        def equipment_comparison_plot() -> go.Figure:
            return self.create_plot()
