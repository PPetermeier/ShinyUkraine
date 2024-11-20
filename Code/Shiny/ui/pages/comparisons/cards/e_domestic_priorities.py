import plotly.graph_objects as go
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget

from server import load_data_from_table
from server.queries import DOMESTIC_COMPARISON_QUERY, EUROPEAN_CRISIS_QUERY, GERMAN_COMPARISON_QUERY
from config import LAST_UPDATE, COMPARISONS_MARGIN, COLOR_PALETTE

class DomesticPrioritiesCard:
    @staticmethod
    def ui():
        return ui.div(
            ui.div(
                {"class": "text-center mb-4"},
                ui.h3("Support Comparisons"),
                ui.div({"class": "text-muted"}, "Comparing different types of European support"),
            ),
            ui.row(
                {"class": "g-4"},
                ui.column(
                    4,
                    ui.card(
                        {"class": "h-100"},
                        output_widget("crisis_comparison_plot", height="600px"),
                    ),
                ),
                ui.column(
                    4,
                    ui.card(
                        {"class": "h-100"},
                        ui.card_header(
                            ui.div(
                                {"class": "d-flex justify-content-between align-items-center"},
                                ui.div(
                                    {"class": "ms-3"},
                                    ui.input_switch("show_absolute_domestic_values", "Show Absolute Values", value=True)
                                ),
                            ),
                        ),
                        output_widget("domestic_support_plot", height="600px"),
                    ),
                ),
                ui.column(
                    4,
                    ui.card(
                        {"class": "h-100"},
                        output_widget("german_spending_plot", height="600px"),
                    ),
                ),
            ),
        )

class DomesticPrioritiesServer:
    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
        self.domestic_data = load_data_from_table(DOMESTIC_COMPARISON_QUERY)
        self.crisis_data = load_data_from_table(EUROPEAN_CRISIS_QUERY)
        self.german_data = load_data_from_table(GERMAN_COMPARISON_QUERY)
        
    def create_german_spending_plot(self):
        display_names = {
            "Energy subsidies for households and firms (\"Doppelwumms\")": "Energy Subsidies HHs & firms",
            "Special military fund (\"Sondervermögen Bundeswehr\") ": "Special Military Fund",
            "German aid to Ukraine": "Aid to Ukraine",
            "Rescue of Uniper (incl. EU shares)": "Rescue Uniper, total",
            "Transport Subsidies (\"Tankrabatt\" & \"9€ Ticket\")": "Transport Subsidies"
        }
        
        programs = [
            {
                "name": display_names[row["commitments"]],
                "original_name": row["commitments"],
                "value": row["cost"] if row["cost"] > 0 else row["total_bilateral_aid"],
                "color": COLOR_PALETTE[row["commitments"]]
            }
            for row in self.german_data.to_dict('records')
        ]
        
        fig = go.Figure()
        
        # Create traces (no need to sort the data beforehand)
        for program in programs:
            fig.add_trace(
                go.Bar(
                    y=[program["name"]],
                    x=[program["value"]],
                    orientation="h",
                    name=program["name"],
                    marker_color=program["color"],
                    text=f"{program['value']:.1f}B€",
                    textposition="auto",
                    hovertemplate="%{y}<br>Amount: %{x:.1f}B€",
                )
            )

        fig.update_layout(
            height=550,
            margin=COMPARISONS_MARGIN,
            template="plotly_white",
            xaxis_title="Billion €",
            title=dict(
                text=(
                    "German Support Programs (2022)<br>"
                    f"<span style='font-size: 12px; color: gray;'>"
                    "Comparing domestic spending with Ukraine aid"
                    f"<br>Last updated: {LAST_UPDATE}, Sheet: Fig 21</span>"
                ),
                x=0.5,
                y=0.95,
            ),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.1,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.1)",
                borderwidth=1,
            ),
            yaxis=dict(
                title="",
                categoryorder='total ascending',  # This will order bars by their values
                showticklabels=True
            ),
            barmode="group",
            hovermode="y unified",
        )
        return fig

    def create_crisis_comparison_plot(self):
        fig = go.Figure()
        
        # Create traces
        for commitment, value in zip(self.crisis_data["commitments"], self.crisis_data["total_support__billion"]):
            fig.add_trace(
                go.Bar(
                    y=[commitment],
                    x=[value],
                    orientation="h",
                    name=commitment,
                    marker_color=COLOR_PALETTE[commitment],
                    text=f"{value:.1f}B€",
                    textposition="auto",
                    hovertemplate="%{y}<br>Amount: %{x:.1f}B€",
                )
            )

        fig.update_layout(
            height=550,
            margin=COMPARISONS_MARGIN,
            template="plotly_white",
            xaxis_title="Billion €",
            title=dict(
                text=(
                    "Europe's Response to Major Crises<br>"
                    f"<span style='font-size: 12px; color: gray;'>"
                    "Comparing support across different European crises"
                    f"<br>Last updated: {LAST_UPDATE}, Sheet: Fig 19</span>"
                ),
                x=0.5,
                y=0.95,
            ),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.1,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.1)",
                borderwidth=1,
            ),
            yaxis=dict(
                title="",
                categoryorder='total ascending',  # This will order bars by their values
                showticklabels=True
            ),
            hovermode="y unified",
        )
        return fig

    def create_domestic_support_plot(self):
        show_absolute_values = self.input.show_absolute_domestic_values()
        value_suffix = 'B€' if show_absolute_values else '%'
        
        if show_absolute_values:
            fiscal_values = self.domestic_data["fiscal_abs"].tolist()
            ukraine_values = self.domestic_data["ukraine_abs"].tolist()
            y_axis_title = "Billion €"
        else:
            fiscal_values = self.domestic_data["fiscal_gdp"].tolist()
            ukraine_values = self.domestic_data["ukraine_gdp"].tolist()
            y_axis_title = "percent of GDP"
        
        countries = self.domestic_data["countries"].tolist()
        
        fig = go.Figure()
        
        fig.add_trace(
            go.Bar(
                y=countries,
                x=fiscal_values,
                name="Fiscal commitments for energy subsidies",
                marker_color=COLOR_PALETTE["Fiscal commitments for energy subsidies"],
                orientation="h",
                text=[f"{x:.2f}{value_suffix}" for x in fiscal_values],
                textposition="auto",
                customdata=list(zip(fiscal_values, ukraine_values)),
                hovertemplate=(
                    "%{y}<br>" +
                    f"Energy Subsidies: %{{customdata[0]:.2f}}{value_suffix}<br>" +
                    f"Ukraine Aid: %{{customdata[1]:.2f}}{value_suffix}"
                ),
            )
        )
        
        fig.add_trace(
            go.Bar(
                y=countries,
                x=ukraine_values,
                name="Aid for Ukraine (incl. EU share)",
                marker_color=COLOR_PALETTE["Aid for Ukraine (incl. EU share)"],
                orientation="h",
                text=[f"{x:.2f}{value_suffix}" for x in ukraine_values],
                textposition="auto",
                customdata=list(zip(fiscal_values, ukraine_values)),
                hovertemplate=(
                    "%{y}<br>" +
                    f"Energy Subsidies: %{{customdata[0]:.2f}}{value_suffix}<br>" +
                    f"Ukraine Aid: %{{customdata[1]:.2f}}{value_suffix}"
                ),
            )
        )
        
        fig.update_layout(
            height=550,
            margin=COMPARISONS_MARGIN,
            template="plotly_white",
            xaxis_title=y_axis_title,
            title=dict(
                text=(
                    "Domestic Energy Support vs Ukraine Aid<br>"
                    f"<span style='font-size: 12px; color: gray;'>"
                    "Comparing support across European countries"
                    f"<br>Last updated: {LAST_UPDATE}, Sheet: Fig 20</span>"
                ),
                x=0.5,
                y=0.95,
            ),
            barmode="group",
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.1,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.1)",
                borderwidth=1,
            ),
            yaxis=dict(
                title="",
                categoryorder='total ascending',  # This will order bars by the sum of values in each category
                showticklabels=True
            ),
            hovermode="y unified",
        )
        return fig


    def register_outputs(self):
        @self.output
        @render_widget
        def crisis_comparison_plot():
            return self.create_crisis_comparison_plot()

        @self.output
        @render_widget
        def domestic_support_plot():
            return self.create_domestic_support_plot()

        @self.output
        @render_widget
        def german_spending_plot():
            return self.create_german_spending_plot()