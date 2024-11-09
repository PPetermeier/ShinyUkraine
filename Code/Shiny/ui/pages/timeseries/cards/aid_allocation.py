"""
Aid allocation visualization card grouped by country categories.
"""

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE
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
                ui.h3("Aid Allocation by Country Groups, commited vs allocated"),
                ui.div({"class": "card-subtitle text-muted"}, "Visualization of aid commitments and allocations grouped by country categories"),
            ),
            ui.layout_sidebar(
                ui.sidebar(
                    "Input options",
                    ui.input_checkbox_group(
                        "country_groups",
                        "Select Country Groups",
                        choices=COUNTRY_GROUPS,
                        selected=["EU_member", "EU_institutions", "Anglosaxon_countries", "Other_donor_countries"],
                    ),
                    position="fixed",
                    min_width="300px",
                    max_width="300px",
                    bg="#f8f8f8",
                ),
                output_widget("allocation_plot"),
            ),
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
            # Now we only need selected_groups since we removed aid type selection
            query = build_group_allocations_query(
                aid_type="total",  # hardcoded since we only have total
                selected_groups=self.input.country_groups(),
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
            "Other_donor_countries": COLOR_PALETTE["total"],
        }

        # Create a copy of the data to avoid modifying the original
        plot_data = data.copy()
        # Replace technical names with display names
        plot_data["group_name"] = plot_data["group_name"].map(name_mapping)

        fig = go.Figure()

        # First add committed aid bars (total height)
        fig.add_trace(
            go.Bar(
                name="Committed Aid",
                x=plot_data["group_name"],
                y=plot_data["committed_aid"],
                marker_color=[desaturate_color(color_mapping[group]) for group in data["group_name"]],
                hovertemplate="%{x}<br>Committed: %{y:.1f}B €<extra></extra>",
                opacity=0.7,  # Added opacity to better show the overlay effect
            )
        )

        # Then add allocated aid bars (will appear in front)
        fig.add_trace(
            go.Bar(
                name="Allocated Aid",
                x=plot_data["group_name"],
                y=plot_data["allocated_aid"],
                marker_color=[color_mapping[group] for group in data["group_name"]],
                hovertemplate="%{x}<br>Allocated: %{y:.1f}B €<extra></extra>",
            )
        )

        fig.update_layout(
            title="Aid Allocation by Country Groups",
            xaxis_title="Country Groups",
            yaxis_title="Billion € ",
            barmode="overlay",
            template="plotly_white",
            height=600,
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.01,
                bgcolor="rgba(255, 255, 255, 0.8)",
                itemsizing="constant",
            ),
            showlegend=False,
            hovermode="x unified",
            yaxis=dict(
                showgrid=False,
                gridcolor="rgba(0,0,0,0.1)",
                zerolinecolor="rgba(0,0,0,0.2)",
            ),
            xaxis=dict(
                showgrid=False,
                gridcolor="rgba(0,0,0,0.1)",
                zerolinecolor="rgba(0,0,0,0.2)",
                categoryorder="total descending",  # Changed to descending to show largest first
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
