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
        # Define display name mapping with exact keys from the database
        display_names = {
            "Energy subsidies for households and firms (\"Doppelwumms\")": "Energy Subsidies HHs & firms",
            "Special military fund (\"Sondervermögen Bundeswehr\") ": "Special Military Fund",  # Note the extra space
            "German aid to Ukraine": "Aid to Ukraine",
            "Rescue of Uniper (incl. EU shares)": "Rescue Uniper, total",
            "Transport Subsidies (\"Tankrabatt\" & \"9€ Ticket\")": "Transport Subsidies"
        }
        
        # Define colors mapping with the same exact keys
        color_mapping = {
            "Energy subsidies for households and firms (\"Doppelwumms\")": "#FFD700",
            "Special military fund (\"Sondervermögen Bundeswehr\") ": "#FFA500",  # Note the extra space
            "German aid to Ukraine": "#4169E1",
            "Rescue of Uniper (incl. EU shares)": "#DAA520",
            "Transport Subsidies (\"Tankrabatt\" & \"9€ Ticket\")": "#F4C430"
        }
        
        # Get the data from self.german_data and create programs list
        programs = [
            {
                "name": display_names[row["commitments"]],  # Use display name
                "original_name": row["commitments"],  # Keep original name for color mapping
                "value": row["cost"] if row["cost"] > 0 else row["total_bilateral_aid"],
                "color": color_mapping[row["commitments"]]
            }
            for row in self.german_data.to_dict('records')
        ]
        
        # Sort programs by value in ascending order
        programs.sort(key=lambda x: x["value"])
        
        # Extract sorted program names, values, and colors
        program_names = [program["name"] for program in programs]
        values = [program["value"] for program in programs]
        colors = [program["color"] for program in programs]
        
        fig = go.Figure()
        
        # Create separate trace for each program
        for program_name, value, color in zip(program_names, values, colors):
            fig.add_trace(
                go.Bar(
                    y=[program_name],
                    x=[value],
                    orientation="h",
                    name=program_name,
                    marker_color=color,
                    text=f"{value:.1f}B€",
                    textposition="auto",
                ),
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
                    f"<br>Last updated: {LAST_UPDATE}</span>"
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
                showticklabels=False
            ),
            barmode="group"
        )
        return fig

    def create_crisis_comparison_plot(self):
        commitments = self.crisis_data["commitments"].tolist()
        values = self.crisis_data["total_support__billion"].tolist()
        fig = go.Figure()
        
        # Create traces using the commitments as trace names
        for commitment, value in zip(commitments, values):
            fig.add_trace(
                go.Bar(
                    y=[commitment],  # Single value as list for each trace
                    x=[value],
                    orientation="h",
                    name=commitment,  # Use commitment as the legend name
                    marker_color="#FFD700" if commitment != commitments[-1] else "#4169E1",
                    text=f"{value:.1f}B€",
                    textposition="auto",
                ),
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
                    f"<br>Last updated: {LAST_UPDATE}</span>"
                ),
                x=0.5,
                y=0.95,
            ),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.1,  # Positioned above the plot but below the title
                xanchor="center",
                x=0.5,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.1)",
                borderwidth=1,
            ),
            # Remove y-axis title since we're using these values in the legend
            yaxis=dict(
                title="",
                showticklabels=False  # Optional: hide y-axis labels if you don't want them duplicated
            )
        )
        return fig

    def create_domestic_support_plot(self):
        show_absolute_values = self.input.show_absolute_domestic_values()
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
                marker_color="#FFD700",
                orientation="h",
                text=[f"{x:.2f}{'B€' if show_absolute_values else '%'}" for x in fiscal_values],
                textposition="auto",
            ),
        )
        
        fig.add_trace(
            go.Bar(
                y=countries,
                x=ukraine_values,
                name="Aid for Ukraine (incl. EU share)",
                marker_color="#4169E1",
                orientation="h",
                text=[f"{x:.2f}{'B€' if show_absolute_values else '%'}" for x in ukraine_values],
                textposition="auto",
            ),
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
                    f"<br>Last updated: {LAST_UPDATE}</span>"
                ),
                x=0.5,
                y=0.95,
            ),
            barmode="group",
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.1,  # Positioned above the plot but below the title
                xanchor="center",
                x=0.5,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.1)",
                borderwidth=1,
            ),
            # Since we want to keep country names on y-axis, we'll just update the title
            yaxis=dict(
                title="",  # Remove y-axis title since it's not needed
                showticklabels=True  # Keep country labels visible
            )
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