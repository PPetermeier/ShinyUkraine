"""
Aid allocation visualization card grouped by country categories.
"""

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
    """UI components for the aid allocation by country groups card."""

    @staticmethod
    def ui():
        """Return the card UI elements."""
        return ui.card(
            ui.card_header(
                ui.h3("Aid Allocation by Country Groups, committed vs allocated"),
                ui.div(
                    {"class": "card-subtitle text-muted"},
                    "Visualization of aid commitments and allocations grouped by country categories. "
                    "Click legend items to show/hide groups. Double-click to isolate a group.",
                ),
            ),
            output_widget("allocation_plot"),
            height="800px",
        )


class AidAllocationServer:
    """Server logic for the aid allocation card."""

    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
        self._filtered_data = reactive.Calc(self._compute_filtered_data)
        self.register_outputs()

    def _compute_filtered_data(self):
        """Compute filtered data based on user inputs."""
        try:
            # Load data for all groups
            query = build_group_allocations_query(
                aid_type="total",
                selected_groups=list(COUNTRY_GROUPS.keys()),
            )
            return load_data_from_table(query)

        except Exception as e:
            print(f"Error in _compute_filtered_data: {str(e)}")
            return pd.DataFrame(columns=["group_name", "allocated_aid", "committed_aid"])

    def create_plot(self):
        """Create and return the plot figure."""
        data = self._filtered_data()

        if data.empty:
            return go.Figure()

        # Create mapping for display names
        name_mapping = {
            "EU_member": "EU Members",
            "EU_institutions": "EU Institutions",
            "Anglosaxon_countries": "Anglo-Saxon Countries",
            "Other_donor_countries": "Other Donors",
        }

        # Color mapping using existing COLOR_PALETTE
        color_mapping = {
            "EU_member": COLOR_PALETTE["europe"],
            "EU_institutions": COLOR_PALETTE["EU_institutions"],
            "Anglosaxon_countries": COLOR_PALETTE["united_states"],
            "Other_donor_countries": COLOR_PALETTE["other_countries"],
        }

        fig = go.Figure()

        # Sort data by committed aid for consistent ordering
        data = data.sort_values("committed_aid", ascending=True)

        # Add traces for each group
        for _, row in data.iterrows():
            group = row["group_name"]
            display_name = name_mapping[group]
            color = color_mapping[group]

            # Calculate percentage for the hover template
            percentage = (row["allocated_aid"] / row["committed_aid"] * 100) if row["committed_aid"] > 0 else 0

            # Add committed aid bar
            fig.add_trace(
                go.Bar(
                    name=f"{display_name} (Committed)",
                    x=[row["committed_aid"]],
                    y=[display_name],
                    orientation="h",
                    marker_color=desaturate_color(color),
                    legendgroup=display_name,
                    hovertemplate=(f"{display_name}<br>" f"Committed: %{{x:.1f}}B €<br>" f"<extra></extra>"),
                )
            )

            # Add allocated aid bar
            fig.add_trace(
                go.Bar(
                    name=f"{display_name} (Allocated)",
                    x=[row["allocated_aid"]],
                    y=[display_name],
                    orientation="h",
                    marker_color=color,
                    legendgroup=display_name,
                    text=f"{percentage:.1f}%",  # Show percentage on the bar
                    textposition="inside",
                    hovertemplate=(f"{display_name}<br>" f"Allocated: %{{x:.1f}}B €<br>" f"Progress: {percentage:.1f}%" f"<extra></extra>"),
                )
            )
        title = "Aid Allocation Progress by Country Groups"
        fig.update_layout(
            barmode="overlay",
            title=dict(
                text=f"{title}<br><sub>Last updated: {LAST_UPDATE}, Sheet: Fig 5</sub>",
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
                yanchor="bottom",  # Changed from top to bottom
                y=0.01,  # Changed from 0.99 to 0.01
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

        return fig

    def register_outputs(self):
        """Register all outputs for the module."""

        @self.output
        @render_widget
        def allocation_plot():
            return self.create_plot()
