"""
Aid allocation visualization card showing allocated vs committed aid.
"""

import plotly.graph_objects as go
from config import COLOR_PALETTE, LAST_UPDATE, MARGIN
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
                    {"class": "d-flex justify-content-between"},
                    ui.div(
                        {"class": "card-subtitle text-muted"},
                        "Includes bilateral allocations to Ukraine. Allocations are defined as aid "
                        "which has been delivered or specified for delivery. Does not include private donations, "
                        "support for refugees outside of Ukraine, and aid by international organizations.",
                    ),
                    ui.div(
                        {"class": "d-flex align-items-right gap-4"},
                        ui.div(
                            {"class": "d-flex align-items-center gap-2"},
                            "Percentage",
                            ui.input_switch("show_percentage_commitment_ratio", None, value=False),
                        ),
                        ui.panel_conditional(
                            "input.show_percentage_commitment_ratio",
                            ui.div(
                                {"class": "d-flex align-items-center gap-2"},
                                "Ascending",
                                ui.input_switch("reverse_sort_commitment_ratio", None, value=False),
                            ),
                        ),
                        ui.div(
                            {"class": "d-flex align-items-center"},
                            "First  ",
                            ui.input_numeric(
                                "top_n_countries_committment_ratio",
                                None,
                                value=15,
                                min=5,
                                max=50,
                                width="80px",
                            ),
                            " countries",
                        ),
                    ),
                ),
            ),
            output_widget("aid_allocation_plot"),
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
        reverse_sort = self.input.reverse_sort_commitment_ratio()

        if data.empty:
            return go.Figure()

        dynamic_height = max(400, len(data) * 40)
        fig = go.Figure()

        # Get colors from palette
        allocated_color = COLOR_PALETTE.get("aid_delivered", "#1f77b4")  # Default blue if not in palette
        to_allocate_color = COLOR_PALETTE.get("aid_committed", "#ff7f0e")  # Default orange if not in palette

        # Group data by country for easier sorting
        country_data = {}
        for idx, row in data.iterrows():
            if show_percentage:
                x_allocated = row["allocated_pct"]
                x_to_allocate = row["to_be_allocated_pct"]
                hover_suffix = "%"
            else:
                x_allocated = row["allocated_aid"]
                x_to_allocate = row["to_be_allocated"]
                hover_suffix = " Billion €"

            country_data[row["country"]] = {
                "allocated": x_allocated,
                "to_allocate": x_to_allocate,
                "total": x_allocated + x_to_allocate,
            }

        # Sort countries by total value
        sorted_countries = sorted(country_data.keys(), key=lambda x: country_data[x]["total"], reverse=reverse_sort if show_percentage else False)

        # Create two traces, one for allocated and one for to-be-allocated
        allocated_values = []
        to_allocate_values = []
        countries = []

        for country in sorted_countries:
            data = country_data[country]
            allocated_values.append(data["allocated"])
            to_allocate_values.append(data["to_allocate"])
            countries.append(country)

        # Add allocated aid trace
        fig.add_trace(
            go.Bar(
                y=countries,
                x=allocated_values,
                name="Allocated aid",
                orientation="h",
                marker_color=allocated_color,
                hovertemplate="%{y}<br>Allocated: %{x:.1f}" + hover_suffix + "<extra></extra>",
            )
        )

        # Add to-be-allocated aid trace
        fig.add_trace(
            go.Bar(
                y=countries,
                x=to_allocate_values,
                name="Aid to be allocated",
                orientation="h",
                marker_color=to_allocate_color,
                hovertemplate="%{y}<br>To be allocated: %{x:.1f}" + hover_suffix + "<extra></extra>",
            )
        )

        title = "Committed and allocated aid by country"
        fig.update_layout(
            title=dict(
                text=f"{title}<br><sub>Last updated: {LAST_UPDATE}</sub>",
                font=dict(size=14),
                y=0.95,
                x=0.5,
                xanchor="center",
                yanchor="top",
            ),
            barmode="stack",
            xaxis_title="Percent of Committed Aid" if show_percentage else "Billion €",
            template="plotly_white",
            height=dynamic_height,
            margin=MARGIN,
            legend=dict(
                yanchor="bottom",
                y=0.01,
                xanchor="right",
                x=0.99,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.2)",
                borderwidth=1,
            ),
            showlegend=True,
            hovermode="y unified",
            autosize=True,
            yaxis=dict(
                showgrid=False,
                gridcolor="rgba(0,0,0,0.1)",
                zerolinecolor="rgba(0,0,0,0.2)",
                tickfont=dict(size=12),
                categoryorder="total ascending",
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
