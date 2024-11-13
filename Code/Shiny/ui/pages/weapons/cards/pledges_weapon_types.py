from shiny import ui, reactive
from shinywidgets import output_widget, render_widget
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from server.database import load_data_from_table
from server.queries import WEAPON_TYPE_PLEDGES_QUERY
from config import COLOR_PALETTE, MARGIN, LAST_UPDATE
from ui.colorutilities import desaturate_color


class PlegesWeaponTypesCard:
    """UI components for the weapons type pledges visualization card."""

    @staticmethod
    def ui():
        return ui.card(
            ui.card_header(
                ui.div(
                    {"class": "d-flex justify-content-between align-items-center"},
                    ui.div(
                        {"class": "flex-grow-1"},
                        ui.h3("Heavy Weapons Deliveries by Type"),
                        ui.div(
                            {"class": "card-subtitle text-muted"},
                            "Share of national stocks pledged and delivered by weapon type (tanks, howitzers, MLRS)",
                        ),
                    ),
                ),
            ),
            output_widget("weapons_type_pledges_plot"),
        )


class PledgesWeaponTypesServer:
    """Server logic for the weapons type pledges visualization card."""

    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
        self._filtered_data = reactive.Calc(self._compute_filtered_data)

    def _compute_filtered_data(self):
        """Process data for visualization."""
        return load_data_from_table(table_name_or_query=WEAPON_TYPE_PLEDGES_QUERY)

    def create_plot(self):
        """Create the subplot visualization."""
        data = self._filtered_data()

        if data.empty:
            return go.Figure()

        fig = make_subplots(
            rows=3,
            cols=1,
            subplot_titles=("<br><br><br>Tanks", "Howitzers (155/152mm)", "Multiple Launch Rocket Systems"),
            vertical_spacing=0.2,
            shared_yaxes=True,
        )

        # List of weapon types and their data columns
        weapon_types = [
            ("tanks", "tanks_delivered", "tanks_to_deliver"),
            ("howitzers", "howitzers_delivered", "howitzers_to_deliver"),
            ("mlrs", "mlrs_delivered", "mlrs_to_deliver"),
        ]

        # Add traces for each weapon type
        for idx, (weapon_type, delivered_col, to_deliver_col) in enumerate(weapon_types, 1):
            # Sort data for this specific weapon type
            plot_data = data.sort_values(by=[delivered_col, to_deliver_col], ascending=[False, False])

            # Add delivered weapons bars
            fig.add_trace(
                go.Bar(
                    y=plot_data["country"],
                    x=plot_data[delivered_col].multiply(100),  # Convert to percentage
                    name="Delivered",
                    orientation="h",
                    marker_color=COLOR_PALETTE["weapon_stocks_delivered"],
                    hovertemplate="Delivered: %{x:.1f}%<extra></extra>",
                    legendgroup="delivered",
                    showlegend=(idx == 1),  # Show legend only for first subplot
                ),
                row=idx,
                col=1,
            )

            # Add to-be-delivered weapons bars
            fig.add_trace(
                go.Bar(
                    y=plot_data["country"],
                    x=plot_data[to_deliver_col].multiply(100),  # Convert to percentage
                    name="To Be Delivered",
                    orientation="h",
                    marker_color=COLOR_PALETTE["weapon_stocks_pending"],
                    hovertemplate="To Be Delivered: %{x:.1f}%<extra></extra>",
                    legendgroup="to_be_delivered",
                    showlegend=(idx == 1),  # Show legend only for first subplot
                ),
                row=idx,
                col=1,
            )

        # Calculate dynamic height based on number of countries
        plot_height = max(600, len(data) * 30 * 3)  # 30px per country * 3 plots

        # Update layout
        fig.update_layout(
            title=dict(
                text=f"Heavy Weapons Deliveries by Type<br><sub>Last updated: {LAST_UPDATE}</sub>",
                font=dict(size=14),
                y=0.98,
                x=0.5,
                xanchor="center",
                yanchor="top",
                pad=dict(b=20),
            ),
            height=plot_height,
            margin=dict(
                t=120,  # Increase top margin
                b=20,
                l=20,
                r=20,
            ),
            barmode="stack",
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, traceorder="normal"),
            plot_bgcolor="rgba(255,255,255,1)",
            paper_bgcolor="rgba(255,255,255,1)",
        )

        # Update all xaxes
        for i in range(1, 4):
            fig.update_xaxes(title="Share of National Stock (%)", showgrid=True, gridcolor="rgba(0,0,0,0.1)", ticksuffix="%", row=i, col=1)

        # Update all yaxes
        for i in range(1, 4):
            fig.update_yaxes(autorange="reversed", showgrid=False, gridcolor="rgba(0,0,0,0.1)", zerolinecolor="rgba(0,0,0,0.2)", row=i, col=1)

        return fig

    def register_outputs(self):
        """Register all outputs for the module."""

        @self.output
        @render_widget
        def weapons_type_pledges_plot():
            return self.create_plot()
