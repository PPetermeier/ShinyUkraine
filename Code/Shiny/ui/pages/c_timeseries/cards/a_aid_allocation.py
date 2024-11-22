"""Module for visualizing aid allocations by country groups.

This module provides components for creating and managing an interactive visualization
that compares committed versus allocated aid across different country groups,
with support for toggling visibility of individual groups.
"""

from typing import Dict

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE, LAST_UPDATE, MARGIN
from server import (
    COUNTRY_GROUPS,
    build_group_allocations_query,
    load_data_from_table,
)
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget
from ....colorutilities import desaturate_color


class AidAllocationCard:
    """UI components for the aid allocation by country groups card.

    This class handles the user interface elements for displaying the aid
    allocation comparison across country groups.
    """

    @staticmethod
    def ui() -> ui.card:
        """Create the user interface elements for the visualization card.

        Returns:
            ui.card: A Shiny card containing the visualization.
        """
        return ui.card(
            ui.card_header(
                ui.h3("Aid Allocation by Country Groups, committed vs allocated"),
                ui.div(
                    {"class": "card-subtitle text-muted"},
                    "This figure shows total allocations and the remaining amount of total bilateral aid commitments to Ukraine, in billion Euros, across different donor groups between January 24, 2022 and August 31, 2024. Allocations are defined as aid which has been delivered or specified for delivery. Aid remaining to be allocated is calculated as the difference between committed aid and realized allocations. Exchange rate fluctuations, accounting approximations by the donor, or variation in prices and evaluations of specific items within previously committed amounts may lead to allocated aid being smaller than previously committed amounts.",
                ),
            ),
            output_widget("allocation_plot"),
            height="800px",
        )


class AidAllocationServer:
    """Server logic for the aid allocation visualization.

    This class handles data processing and plot generation for the aid allocation
    visualization comparing commitments and allocations across country groups.

    Attributes:
        input: Shiny input object containing user interface values.
        output: Shiny output object for rendering visualizations.
        session: Shiny session object.
    """

    # Define country group configurations
    COUNTRY_GROUP_CONFIG: Dict[str, Dict[str, str]] = {
        "EU_member": {"display_name": "EU Members", "color_key": "Europe"},
        "EU_institutions": {
            "display_name": "EU Institutions",
            "color_key": "EU Institutions",
        },
        "Anglosaxon_countries": {
            "display_name": "Anglo-Saxon Countries",
            "color_key": "United States",
        },
        "Other_donor_countries": {
            "display_name": "Other Donors",
            "color_key": "Other Countries",
        },
    }

    # Define trace configurations
    TRACE_TYPES: Dict[str, Dict[str, object]] = {
        "committed": {
            "name_suffix": "(Committed)",
            "use_desaturated_color": True,
            "text_position": "outside",
            "text_color": "black",
            "hover_template": "<br>Committed: %{x:.1f}B€<extra></extra>",
            "text_format": lambda x: f"{x:.1f}B €",
        },
        "allocated": {
            "name_suffix": "(Allocated)",
            "use_desaturated_color": False,
            "text_position": "inside",
            "text_color": "white",
            "hover_template": "<br>Allocated: %{x:.1f}B€<extra></extra>",
            "text_format": lambda x: f"{x:.1f}%",
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
        self.register_outputs()

    def _compute_filtered_data(self) -> pd.DataFrame:
        """Compute filtered data based on user inputs.

        Returns:
            pd.DataFrame: Filtered DataFrame containing aid allocation data.
        """
        try:
            query = build_group_allocations_query(
                aid_type="total",
                selected_groups=list(COUNTRY_GROUPS.keys()),
            )
            return load_data_from_table(query)

        except Exception as e:
            print(f"Error in _compute_filtered_data: {str(e)}")
            return pd.DataFrame(
                columns=["group_name", "allocated_aid", "committed_aid"]
            )

    def create_plot(self) -> go.Figure:
        """Generate the aid allocation visualization plot.

        Returns:
            go.Figure: Plotly figure object containing the bar chart.
        """
        data = self._filtered_data()
        if data.empty:
            return go.Figure()

        # Sort data by committed aid for consistent ordering
        data = data.sort_values("committed_aid", ascending=True)

        fig = self._create_bar_chart(data)
        self._update_figure_layout(fig)

        return fig

    def _create_bar_chart(self, data: pd.DataFrame) -> go.Figure:
        """Create a bar chart visualization.

        Args:
            data: DataFrame containing filtered aid allocation data.

        Returns:
            go.Figure: Configured bar chart figure.
        """
        fig = go.Figure()

        for _, row in data.iterrows():
            group_config = self.COUNTRY_GROUP_CONFIG[row["group_name"]]
            display_name = group_config["display_name"]
            base_color = COLOR_PALETTE[group_config["color_key"]]

            # Calculate percentage for allocated aid text
            percentage = (
                (row["allocated_aid"] / row["committed_aid"] * 100)
                if row["committed_aid"] > 0
                else 0
            )

            # Add traces for committed and allocated aid
            self._add_aid_traces(
                fig=fig,
                display_name=display_name,
                committed_aid=row["committed_aid"],
                allocated_aid=row["allocated_aid"],
                percentage=percentage,
                base_color=base_color,
            )

        return fig

    def _add_aid_traces(
        self,
        fig: go.Figure,
        display_name: str,
        committed_aid: float,
        allocated_aid: float,
        percentage: float,
        base_color: str,
    ) -> None:
        """Add committed and allocated aid traces to the figure.

        Args:
            fig: Plotly figure to add traces to.
            display_name: Display name for the country group.
            committed_aid: Amount of committed aid.
            allocated_aid: Amount of allocated aid.
            percentage: Percentage of allocation vs commitment.
            base_color: Base color for the traces.
        """
        # Add committed aid trace
        fig.add_trace(
            self._create_bar_trace(
                name=f"{display_name} {self.TRACE_TYPES['committed']['name_suffix']}",
                value=committed_aid,
                display_name=display_name,
                color=desaturate_color(base_color)
                if self.TRACE_TYPES["committed"]["use_desaturated_color"]
                else base_color,
                text=self.TRACE_TYPES["committed"]["text_format"](committed_aid),
                text_position=self.TRACE_TYPES["committed"]["text_position"],
                text_color=self.TRACE_TYPES["committed"]["text_color"],
                hover_template=f"{display_name}{self.TRACE_TYPES['committed']['hover_template']}",
            )
        )

        # Add allocated aid trace
        fig.add_trace(
            self._create_bar_trace(
                name=f"{display_name} {self.TRACE_TYPES['allocated']['name_suffix']}",
                value=allocated_aid,
                display_name=display_name,
                color=base_color,
                text=self.TRACE_TYPES["allocated"]["text_format"](percentage),
                text_position=self.TRACE_TYPES["allocated"]["text_position"],
                text_color=self.TRACE_TYPES["allocated"]["text_color"],
                hover_template=f"{display_name}{self.TRACE_TYPES['allocated']['hover_template']}",
            )
        )

    def _create_bar_trace(
        self,
        name: str,
        value: float,
        display_name: str,
        color: str,
        text: str,
        text_position: str,
        text_color: str,
        hover_template: str,
    ) -> go.Bar:
        """Create a bar trace for the visualization.

        Args:
            name: Name for the trace.
            value: Value for the bar.
            display_name: Display name for the group.
            color: Color for the bar.
            text: Text to display on the bar.
            text_position: Position of the text.
            text_color: Color of the text.
            hover_template: Template for hover text.

        Returns:
            go.Bar: Configured bar trace.
        """
        return go.Bar(
            name=name,
            x=[value],
            y=[display_name],
            orientation="h",
            marker_color=color,
            legendgroup=display_name,
            text=text,
            textposition=text_position,
            textfont=dict(color=text_color),
            hovertemplate=hover_template,
            showlegend=True,
        )

    def _update_figure_layout(self, fig: go.Figure) -> None:
        """Update the layout of the figure.

        Args:
            fig: Plotly figure object to update.
        """
        fig.update_layout(
            barmode="overlay",
            title=dict(
                text=f"Aid Allocation Progress by Country Groups<br>"
                f"<sub>Last updated: {LAST_UPDATE}, Sheet: Fig 5</sub>",
                font=dict(size=14),
                y=0.95,
                x=0.5,
                xanchor="center",
                yanchor="top",
            ),
            xaxis_title="Billion €",
            template="plotly_white",
            height=600,
            margin=MARGIN,
            legend=dict(
                yanchor="bottom",
                y=0.01,
                xanchor="right",
                x=0.99,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.2)",
                borderwidth=1,
                itemsizing="constant",
                groupclick="toggleitem",
            ),
            showlegend=True,
            hovermode="y unified",
            yaxis=dict(
                showgrid=False,
                gridcolor="rgba(0,0,0,0.1)",
                zerolinecolor="rgba(0,0,0,0.2)",
            ),
            xaxis=dict(
                showgrid=True,
                gridcolor="rgba(0,0,0,0.1)",
                zerolinecolor="rgba(0,0,0,0.2)",
            ),
            plot_bgcolor="rgba(255,255,255,1)",
            paper_bgcolor="rgba(255,255,255,1)",
        )

    def register_outputs(self) -> None:
        """Register the plot output with Shiny."""

        @self.output
        @render_widget
        def allocation_plot():
            return self.create_plot()
