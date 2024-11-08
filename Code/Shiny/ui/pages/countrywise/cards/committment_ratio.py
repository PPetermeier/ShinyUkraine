"""
Aid allocation visualization card showing allocated vs committed aid.
"""

import plotly.graph_objects as go
from config import COLOR_PALETTE
from server import load_data_from_table
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget

from ui.colorutilities import desaturate_color


class CommittmentRatioCard:
    """UI components for the aid allocation visualization card."""

    @staticmethod
    def ui():
        """Return the card UI elements."""
        return ui.card(
            ui.card_header(
                ui.h3("Aid Allocation Progress"),
                ui.div(
                    {"class": "card-subtitle text-muted"},
                    "Includes bilateral allocations to Ukraine. Allocations are defined as aid "
                    "which has been delivered or specified for delivery. Does not include private donations, "
                    "support for refugees outside of Ukraine, and aid by international organizations.",
                ),
            ),
            ui.layout_sidebar(
                ui.sidebar(
                    "Input options",
                    ui.input_switch("show_percentage_commitment_ratio", "Show as Percentage", value=False),
                    ui.panel_conditional(
                        "input.show_percentage_commitment_ratio", ui.input_switch("reverse_sort_commitment_ratio", "Reverse Sort Order", value=False)
                    ),
                    ui.input_numeric("top_n_countries_committment_ratio", "Show Top N Countries", value=15, min=5, max=50),
                    position="fixed",
                    min_width="300px",
                    max_width="300px",
                    bg="#f8f8f8",
                ),
                output_widget("aid_allocation_plot"),
            ),
            height="800px",
        )


class CommittmentRatioServer:
    """Server logic for the aid allocation visualization card."""

    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
        self.df = load_data_from_table("d_allocations_vs_commitments")

        # Calculate to-be-allocated amount and delivery ratio
        if "allocated_aid" in self.df.columns and "committed_aid" in self.df.columns:
            self.df["to_be_allocated"] = self.df["committed_aid"] - self.df["allocated_aid"]
            self.df["delivery_ratio"] = self.df["allocated_aid"] / self.df["committed_aid"]

        self._filtered_data = reactive.Calc(self._compute_filtered_data)
        self.register_outputs()

    def _compute_filtered_data(self):
        """Filter and process data based on user selections."""
        result = self.df.copy()
        show_percentage = self.input.show_percentage_commitment_ratio()
        reverse_sort = self.input.reverse_sort_commitment_ratio()

        if show_percentage:
            # Calculate percentages
            result["allocated_pct"] = (result["allocated_aid"] / result["committed_aid"]) * 100
            result["to_be_allocated_pct"] = (result["to_be_allocated"] / result["committed_aid"]) * 100

            # Sort by delivery ratio
            ascending = not reverse_sort  # True if reverse_sort is False, False if reverse_sort is True
            result = result.nlargest(self.input.top_n_countries_committment_ratio(), "committed_aid")
            result = result.sort_values("delivery_ratio", ascending=ascending)
        else:
            # For absolute values, sort by committed aid
            result = result.nlargest(self.input.top_n_countries_committment_ratio(), "committed_aid")
            result = result.sort_values("committed_aid", ascending=True)

        return result

    def create_plot(self):
        """Create and return the plot figure."""
        data = self._filtered_data()
        show_percentage = self.input.show_percentage_commitment_ratio()

        if data.empty:
            return go.Figure()

        fig = go.Figure()

        # Use country-specific colors
        for idx, row in data.iterrows():
            country_color = COLOR_PALETTE.get(row["country"], "#333333")
            desaturated_color = desaturate_color(country_color)

            if show_percentage:
                x_allocated = row["allocated_pct"]
                x_to_allocate = row["to_be_allocated_pct"]
                hover_suffix = "%"
            else:
                x_allocated = row["allocated_aid"]
                x_to_allocate = row["to_be_allocated"]
                hover_suffix = " Billion €"

            # Allocated aid bar
            fig.add_trace(
                go.Bar(
                    y=[row["country"]],
                    x=[x_allocated],
                    name="Allocated aid" if (idx == 0 and not show_percentage) else None,  # Only show legend for non-percentage view
                    orientation="h",
                    marker_color=country_color,
                    showlegend=(idx == 0 and not show_percentage),  # Only show legend for non-percentage view
                    hovertemplate="%{y}<br>Allocated: %{x:.1f}" + hover_suffix + "<extra></extra>",
                )
            )

            # Aid to be allocated bar
            fig.add_trace(
                go.Bar(
                    y=[row["country"]],
                    x=[x_to_allocate],
                    name="Aid to be allocated" if (idx == 0 and not show_percentage) else None,  # Only show legend for non-percentage view
                    orientation="h",
                    marker_color=desaturated_color,
                    showlegend=(idx == 0 and not show_percentage),  # Only show legend for non-percentage view
                    hovertemplate="%{y}<br>To be allocated: %{x:.1f}" + hover_suffix + "<extra></extra>",
                )
            )

        fig.update_layout(
            barmode="stack",
            xaxis_title="Percent of Committed Aid" if show_percentage else "Billion €",
            template="plotly_white",
            height=600,
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(yanchor="bottom", y=0.01, xanchor="right", x=0.99, bgcolor="rgba(255, 255, 255, 0.8)", bordercolor="rgba(0, 0, 0, 0.2)", borderwidth=1),
            showlegend=not show_percentage,  # Only show legend for non-percentage view
            hovermode="y unified",
            autosize=True,
            yaxis=dict(
                showgrid=False,
                gridcolor="rgba(0,0,0,0.1)",
                zerolinecolor="rgba(0,0,0,0.2)",
            ),
            xaxis=dict(
                showgrid=False,
                gridcolor="rgba(0,0,0,0.1)",
                zerolinecolor="rgba(0,0,0,0.2)",
                range=[0, 100] if show_percentage else None,
            ),
            plot_bgcolor="rgba(255,255,255,1)",
            paper_bgcolor="rgba(255,255,255,1)",
        )

        return fig

    def register_outputs(self):
        """Register all outputs for the module."""

        @self.output
        @render_widget
        def aid_allocation_plot():
            return self.create_plot()
