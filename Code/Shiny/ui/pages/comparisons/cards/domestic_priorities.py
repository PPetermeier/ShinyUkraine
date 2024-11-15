import plotly.graph_objects as go
from plotly.subplots import make_subplots
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget

from server import load_data_from_table
from server.queries import DOMESTIC_COMPARISON_QUERY, EUROPEAN_CRISIS_QUERY, GERMAN_COMPARISON_QUERY
from config import LAST_UPDATE, COMPARISONS_MARGIN, COLOR_PALETTE


class DomesticPrioritiesCard:
    @staticmethod
    def ui():
        return ui.card(
            ui.card_header(
                ui.div(
                    {"class": "d-flex justify-content-between align-items-center"},
                    ui.div(
                        {"class": "flex-grow-1"},
                        ui.h3("Support Comparisons"),
                        ui.div({"class": "card-subtitle text-muted mb-4"}, "Comparing different types of European support"),
                    ),
                    ui.div({"class": "ms-3"}, ui.input_switch("show_absolute_domestic_values", "Show Absolute Values", value=True)),
                ),
            ),
            output_widget("domestic_comparison_plot", height="auto"),
        )


class DomesticPrioritiesServer:
    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
        # Load data for both plots
        self.domestic_data = load_data_from_table(DOMESTIC_COMPARISON_QUERY)
        self.crisis_data = load_data_from_table(EUROPEAN_CRISIS_QUERY)
        self.german_data = load_data_from_table(GERMAN_COMPARISON_QUERY)

    def create_european_crisis_plot(self, fig):
        """Creates the European crisis comparison plot in the leftmost subplot"""
        commitments = self.crisis_data["commitments"].tolist()
        values = self.crisis_data["total_support__billion"].tolist()

        # Add horizontal bars
        fig.add_trace(
            go.Bar(
                y=commitments,
                x=values,
                orientation="h",
                name="Total Support",
                marker_color=["#FFD700", "#FFD700", "#4169E1"],  # Gold for non-Ukraine, blue for Ukraine
                text=[f"{x:.1f}" for x in values],
                textposition="auto",
                showlegend=False,
            ),
            row=1,
            col=1,
        )

        # Update axes
        fig.update_xaxes(title="Billion €", row=1, col=1, gridcolor="rgba(0,0,0,0.1)")
        fig.update_yaxes(row=1, col=1, gridcolor="rgba(0,0,0,0.1)", showgrid=False)

        return fig

    def create_domestic_comparison_plot(self, fig):
        """Creates the domestic energy vs Ukraine aid plot in the middle subplot"""
        show_absolute_domestic_values = self.input.show_absolute_domestic_values()

        if show_absolute_domestic_values:
            fiscal_values = self.domestic_data["fiscal_abs"].tolist()
            ukraine_values = self.domestic_data["ukraine_abs"].tolist()
            y_axis_title = "Billion €"
        else:
            fiscal_values = self.domestic_data["fiscal_gdp"].tolist()
            ukraine_values = self.domestic_data["ukraine_gdp"].tolist()
            y_axis_title = "percent of GDP"

        countries = self.domestic_data["countries"].tolist()

        # Add traces for domestic comparison
        fig.add_trace(
            go.Bar(
                y=countries,
                x=fiscal_values,
                name="Fiscal commitments for energy subsidies",
                marker_color="#FFD700",  # Gold
                orientation="h",
                text=[f"{x:.2f}" for x in fiscal_values],
                textposition="auto",
            ),
            row=1,
            col=2,
        )

        fig.add_trace(
            go.Bar(
                y=countries,
                x=ukraine_values,
                name="Aid for Ukraine (incl. EU share)",
                marker_color="#4169E1",  # Royal Blue
                orientation="h",
                text=[f"{x:.2f}" for x in ukraine_values],
                textposition="auto",
            ),
            row=1,
            col=2,
        )

        # Update axes
        fig.update_xaxes(title=y_axis_title, row=1, col=2, gridcolor="rgba(0,0,0,0.1)")
        fig.update_yaxes(row=1, col=2, gridcolor="rgba(0,0,0,0.1)",showgrid=False)

        return fig

    def create_german_comparison_plot(self, fig):
        """Creates the German spending comparison plot in the rightmost subplot"""

        data = self.german_data.copy()

        # Create separate dataframes for each type of spending
        cost_data = data[data["cost"] > 0]
        bilateral_data = data[data["total_bilateral_aid"] > 0]
        eu_data = data[data["eu_aid_shares"] > 0]

        # Create traces list
        traces = []

        # Cost trace (yellow)
        if not cost_data.empty:
            cost_trace = go.Bar(
                y=cost_data["description"],
                x=cost_data["cost"],
                orientation="h",
                name="Cost",
                marker_color="#FFD700",  # Gold
                text=cost_data["cost"].apply(lambda x: f"{x:.1f}"),
                textposition="auto",
                hovertemplate="Cost: %{x:.1f} billion€<extra></extra>",
                showlegend=True,
            )
            traces.append(cost_trace)

        # Bilateral aid trace (dark blue)
        if not bilateral_data.empty:
            bilateral_trace = go.Bar(
                y=bilateral_data["description"],
                x=bilateral_data["total_bilateral_aid"],
                orientation="h",
                name="Bilateral Aid",
                marker_color="#0D47A1",  # Dark blue
                text=bilateral_data["total_bilateral_aid"].apply(lambda x: f"{x:.1f}"),
                textposition="auto",
                hovertemplate="Bilateral Aid: %{x:.1f} billion€<extra></extra>",
                showlegend=True,
            )
            traces.append(bilateral_trace)

        # EU shares trace (light blue)
        if not eu_data.empty:
            eu_trace = go.Bar(
                y=eu_data["description"],
                x=eu_data["eu_aid_shares"],
                orientation="h",
                name="EU Shares",
                marker_color="#90CAF9",  # Light blue
                text=eu_data["eu_aid_shares"].apply(lambda x: f"{x:.1f}"),
                textposition="auto",
                hovertemplate="EU Shares: %{x:.1f} billion€<extra></extra>",
                showlegend=True,
            )
            traces.append(eu_trace)

        # Add all traces to the figure
        for trace in traces:
            fig.add_trace(trace, row=1, col=3)

        # Update axes
        fig.update_xaxes(
            title="billion Euros", range=[0, 200], row=1, col=3, showgrid=True, gridcolor="rgba(0,0,0,0.1)", zeroline=True, zerolinecolor="rgba(0,0,0,0.2)"
        )

        fig.update_yaxes(row=1, col=3, showgrid=False, zeroline=True, zerolinecolor="rgba(0,0,0,0.2)")

        # Update layout
        fig.update_layout(barmode="stack", showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

        return fig

    def create_plot(self):
        # Create figure with 3 subplots horizontally arranged
        fig = make_subplots(
            rows=1,
            cols=3,
            subplot_titles=(
                "Europe's response to major crises",
                "Domestic Energy Support vs Ukraine Aid",
                "Germany's spending program in 2022<br>vs aid to Ukraine",
            ),
            column_widths=[0.35, 0.35, 0.3],
            horizontal_spacing=0.08,
        )

        # Add each subplot
        fig = self.create_european_crisis_plot(fig)
        fig = self.create_domestic_comparison_plot(fig)
        fig = self.create_german_comparison_plot(fig)

        # Update layout
        fig.update_layout(
            height=700,
            margin=COMPARISONS_MARGIN,
            template="plotly_white",
            title=dict(
                text=(
                    f"European Support Comparisons<br>"
                    f"<span style='font-size: 12px; color: gray;'>"
                    "Comparing various types of European financial support"
                    f"<br>Last updated: {LAST_UPDATE}</span>"
                ),
                x=0.5,
                y=0.95,
                yanchor="top",
                xanchor="center",
                font=dict(size=16),
                pad=dict(b=20),
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.12,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.2)",
                borderwidth=1,
                itemsizing="constant",
            ),
            showlegend=True,
            barmode="group",
        )

        return fig

    def register_outputs(self):
        @self.output
        @render_widget
        def domestic_comparison_plot():
            return self.create_plot()
