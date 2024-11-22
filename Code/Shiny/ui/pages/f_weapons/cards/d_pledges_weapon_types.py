"""Module for visualizing weapon type pledges by country.

This module provides components for creating and managing interactive visualizations
that show the percentage of national stocks pledged to Ukraine for different types
of weapons (tanks, howitzers, and MLRS). It includes both UI components and server-side
logic for data processing and visualization of each weapon type.
"""

from typing import Any, Dict

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE, COMPARISONS_MARGIN, LAST_UPDATE
from server.database import load_data_from_table
from server.queries import WEAPON_TYPE_PLEDGES_QUERY
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget


class WeaponTypeCard:
    """Base class for individual weapon type visualization cards.

    This class handles the user interface elements for displaying a single weapon
    type visualization.

    Attributes:
        title: Title of the weapon type visualization.
        weapon_type: Identifier for the weapon type.
        delivered_col: Name of the column containing delivered weapons data.
        to_deliver_col: Name of the column containing to-be-delivered weapons data.
    """

    def __init__(self, title: str, weapon_type: str, delivered_col: str, to_deliver_col: str):
        """Initialize the weapon type card.

        Args:
            title: Title for the visualization.
            weapon_type: Identifier for the weapon type.
            delivered_col: Column name for delivered weapons.
            to_deliver_col: Column name for weapons to be delivered.
        """
        self.title = title
        self.weapon_type = weapon_type
        self.delivered_col = delivered_col
        self.to_deliver_col = to_deliver_col

    def ui(self) -> ui.div:
        """Create the user interface elements for the weapon type card.

        Returns:
            ui.div: A Shiny div containing the visualization.
        """
        return ui.card(
            ui.card_header(
                ui.div(
                    {"class": "d-flex justify-content-between align-items-center"},
                    ui.div(
                        {"class": "flex-grow-1"},
                        ui.h3("Heavy Weapons Deliveries"),
                        ui.div(
                            {"class": "card-subtitle text-muted"},
                            "This figure shows estimated values of heavy weapon allocations to Ukraine across the top 20 donors in billion Euros between January 24, 2022 and August 31, 2024. Does not include ammunition of any kind, smaller arms or equipment, and funds committed for future weapons purchases. Allocations are defined as aid which has been delivered or specified for delivery. The values are calculated based on allocated units and our own price estimates for heavy weaponry. Therefore, the values displayed in this figure may not correspond to the amount of military aid displayed in Figure 8.",
                        ),
                    ),
                ),
            ),
            ui.div(
                output_widget(f"weapon_type_{self.weapon_type}_plot"),
            ),
            {"class": "mb-4", "style": "height: 800px;"},
        )


class WeaponTypeServer:
    """Server logic for individual weapon type visualizations.

    This class handles data processing, filtering, and plot generation for a single
    weapon type visualization.

    Attributes:
        input: Shiny input object containing user interface values.
        output: Shiny output object for rendering visualizations.
        session: Shiny session object.
        weapon_type: Identifier for the weapon type.
        delivered_col: Column name for delivered weapons.
        to_deliver_col: Column name for weapons to be delivered.
        title: Title for the visualization.
    """

    # Define visualization properties
    PLOT_CONFIG: Dict[str, Any] = {"marker_color": COLOR_PALETTE["military"], "hover_template": "Pledged: %{x:.1f}%", "height": 600}

    def __init__(self, input: Any, output: Any, session: Any, weapon_type: str, delivered_col: str, to_deliver_col: str, title: str):
        """Initialize the server component.

        Args:
            input: Shiny input object.
            output: Shiny output object.
            session: Shiny session object.
            weapon_type: Identifier for the weapon type.
            delivered_col: Column name for delivered weapons.
            to_deliver_col: Column name for weapons to be delivered.
            title: Title for the visualization.
        """
        self.input = input
        self.output = output
        self.session = session
        self.weapon_type = weapon_type
        self.delivered_col = delivered_col
        self.to_deliver_col = to_deliver_col
        self.title = title
        self._filtered_data = reactive.Calc(self._compute_filtered_data)

    def _compute_filtered_data(self) -> pd.DataFrame:
        """Process and filter data for visualization.

        Returns:
            pd.DataFrame: Filtered DataFrame containing weapon delivery data.
        """
        data = load_data_from_table(table_name_or_query=WEAPON_TYPE_PLEDGES_QUERY)

        # Extract and process weapon-specific data
        weapon_data = data[["country", self.delivered_col, self.to_deliver_col]].copy()
        weapon_data = weapon_data[weapon_data[self.delivered_col].notna() | weapon_data[self.to_deliver_col].notna()]

        # Calculate totals and sort
        weapon_data["total"] = weapon_data[self.delivered_col].fillna(0) + weapon_data[self.to_deliver_col].fillna(0)
        weapon_data = weapon_data.sort_values("total", ascending=False)

        # Filter for delivered weapons and add one zero-delivery country if available
        mask = weapon_data[self.delivered_col] > 0
        delivered_countries = weapon_data[mask]
        if not weapon_data[~mask].empty:
            zero_delivery = weapon_data[~mask].iloc[0:1]
            weapon_data = pd.concat([delivered_countries, zero_delivery])

        return weapon_data

    def create_plot(self) -> go.Figure:
        """Generate the weapon type visualization plot.

        Returns:
            go.Figure: Plotly figure object containing the bar chart.
        """
        data = self._filtered_data()
        if data.empty:
            return go.Figure()

        fig = self._create_bar_chart(data)
        self._update_figure_layout(fig)
        return fig

    def _create_bar_chart(self, data: pd.DataFrame) -> go.Figure:
        """Create a bar chart visualization.

        Args:
            data: DataFrame containing filtered weapon delivery data.

        Returns:
            go.Figure: Configured Plotly figure object.
        """
        fig = go.Figure()
        fig.add_trace(self._create_bar_trace(data))
        return fig

    def _create_bar_trace(self, data: pd.DataFrame) -> go.Bar:
        """Create a bar trace for the visualization.

        Args:
            data: DataFrame containing the visualization data.

        Returns:
            go.Bar: Configured bar trace.
        """
        values = data[self.delivered_col].multiply(100)
        return go.Bar(
            y=data["country"],
            x=values,
            name="Pledged",
            orientation="h",
            marker_color=self.PLOT_CONFIG["marker_color"],
            hovertemplate=self.PLOT_CONFIG["hover_template"],
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
            height=self.PLOT_CONFIG["height"],
            margin=COMPARISONS_MARGIN,
            barmode="stack",
            showlegend=True,
            hovermode="y unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.3, xanchor="center", x=0.5, bgcolor="rgba(255,255,255,0)", bordercolor="rgba(255,255,255,0)"),
            title=dict(
                text=f"{self.title}, pledged by donor country<br>" f"<sub>Last updated: {LAST_UPDATE}, Sheet: Fig 14</sub>",
                y=0.95,
                x=0.5,
                xanchor="center",
                yanchor="top",
                font=dict(size=14),
            ),
            plot_bgcolor="rgba(255,255,255,1)",
            paper_bgcolor="rgba(255,255,255,1)",
        )

        fig.update_xaxes(title="Share of National Stock (%)", showgrid=True, gridcolor="rgba(0,0,0,0.1)", ticksuffix="%")

        fig.update_yaxes(
            autorange="reversed",
            showgrid=False,
            gridcolor="rgba(0,0,0,0.1)",
            zerolinecolor="rgba(0,0,0,0.2)",
            categoryorder="total descending",
        )

    def register_outputs(self) -> None:
        """Register the plot output with Shiny."""

        @self.output(id=f"weapon_type_{self.weapon_type}_plot")
        @render_widget
        def _() -> go.Figure:
            return self.create_plot()


class WeaponTypesCard:
    """Main container for all weapon type visualization cards."""

    WEAPON_TYPES = [
        ("Tanks", "tanks", "tanks_delivered", "tanks_to_deliver"),
        ("Howitzers", "howitzers", "howitzers_delivered", "howitzers_to_deliver"),
        ("MLRS", "mlrs", "mlrs_delivered", "mlrs_to_deliver"),
    ]

    @staticmethod
    def ui() -> ui.div:
        """Create the user interface elements for all weapon type cards.

        Returns:
            ui.div: A Shiny div containing all weapon type visualizations.
        """
        return ui.div(
            *(WeaponTypeCard(title, weapon_type, delivered, to_deliver).ui() for title, weapon_type, delivered, to_deliver in WeaponTypesCard.WEAPON_TYPES)
        )


class WeaponTypesServer:
    """Server logic for all weapon type visualizations.

    This class manages the server components for all weapon type visualizations,
    coordinating their creation and output registration.
    """

    def __init__(self, input: Any, output: Any, session: Any):
        """Initialize all weapon type servers.

        Args:
            input: Shiny input object.
            output: Shiny output object.
            session: Shiny session object.
        """
        self.servers = [
            WeaponTypeServer(input, output, session, weapon_type=wtype, delivered_col=delivered, to_deliver_col=to_deliver, title=title)
            for title, wtype, delivered, to_deliver in WeaponTypesCard.WEAPON_TYPES
        ]

    def register_outputs(self) -> None:
        """Register outputs for all weapon type visualizations."""
        for server in self.servers:
            server.register_outputs()
