import plotly.graph_objects as go
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget

from server import load_data_from_table
from server.queries import GULF_WAR_COMPARISON_QUERY
from config import LAST_UPDATE, COMPARISONS_MARGIN, COLOR_PALETTE

class GulfWarCard:
    @staticmethod
    def ui():
        return ui.card(
            ui.card_header(
                ui.div(
                    {"class": "d-flex justify-content-between align-items-center"},
                    ui.div(
                        {"class": "flex-grow-1"},
                        ui.h3("Gulf War vs Ukraine Aid Comparison"),
                        ui.div(
                            {"class": "card-subtitle text-muted mb-4"},
                            "Gulf War 1990/91 vs. Aid to Ukraine"
                        ),
                    ),
                    ui.div(
                        {"class": "ms-3"},
                        ui.input_switch("show_absolute_gulfwar_values", "Show Absolute Values", value=False)
                    ),
                ),
            ),
            output_widget("gulf_war_plot", height="auto")
        )

class GulfWarServer:
    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
        self.comparison_data = load_data_from_table(GULF_WAR_COMPARISON_QUERY)
        
    def create_plot(self):
            show_absolute_gulfwar_values = self.input.show_absolute_gulfwar_values()
            
            if show_absolute_gulfwar_values:
                gulf_war_values = self.comparison_data['gulf_war_abs'].tolist()
                ukraine_values = self.comparison_data['ukraine_abs'].tolist()
                title_suffix = "expenditures in Billion €"
                y_axis_title = "Billion Euros (2021, inflation adjusted)"
                value_suffix = "B€"
            else:
                gulf_war_values = self.comparison_data['gulf_war_gdp'].tolist()
                ukraine_values = self.comparison_data['ukraine_gdp'].tolist()
                title_suffix = "expenditures in percent of donor GDP"
                y_axis_title = "% of donor GDP"
                value_suffix = "%"
                
            countries = self.comparison_data['countries'].tolist()
                
            fig = go.Figure()
            
            # Gulf War bars
            fig.add_trace(go.Bar(
                x=countries,
                y=gulf_war_values,
                name='Gulf War (1990/91)',
                marker_color=COLOR_PALETTE.get("Gulf War Percentage"),  # Light green
                text=[f"{val:.2f}{value_suffix}" for val in gulf_war_values],
                textposition='auto',
                customdata=[[v1, v2] for v1, v2 in zip(gulf_war_values, ukraine_values)],
                hovertemplate=(
                    "%{x}<br>" +
                    f"Gulf War: %{{y:.2f}}{value_suffix}"
                ),
            ))
            
            # Ukraine aid bars
            fig.add_trace(go.Bar(
                x=countries,
                y=ukraine_values,
                name='Aid to Ukraine',
                marker_color=COLOR_PALETTE.get("Ukraine Yellow"),
                text=[f"{val:.2f}{value_suffix}" for val in ukraine_values],
                textposition='auto',
                customdata=[[v1, v2] for v1, v2 in zip(gulf_war_values, ukraine_values)],
                hovertemplate=(
                    "%{x}<br>" +
                    f"Ukraine Aid: %{{y:.2f}}{value_suffix}"
                ),
            ))
            
            fig.update_layout(
                height=700,
                margin=COMPARISONS_MARGIN,
                xaxis_title=None,
                yaxis_title=y_axis_title,
                template="plotly_white",
                title=dict(
                    text=(
                        f"Gulf War 1990/91 vs. aid to Ukraine, {title_suffix}<br>"
                        f"<span style='font-size: 12px; color: gray;'>"
                        "This figure compares the Gulf War military expenditure with current Ukraine support"
                        f"<br>Last updated: {LAST_UPDATE}. Sheet: Fig 18</span>"
                    ),
                    x=0.5,
                    y=0.95,
                    yanchor='top',
                    xanchor='center',
                    font=dict(size=16),
                    pad=dict(b=20)
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
                    itemsizing='constant'
                ),
                showlegend=True,
                xaxis=dict(
                    showgrid=False,
                    gridcolor="rgba(0,0,0,0.1)",
                    zeroline=True,
                    zerolinecolor="rgba(0,0,0,0.2)"
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="rgba(0,0,0,0.1)",
                    zeroline=True,
                    zerolinecolor="rgba(0,0,0,0.2)"
                ),
                barmode='group',
                autosize=True,
                hovermode="x unified",  # Added unified hover mode (note: using "x" since bars are vertical)
            )
            
            return fig
    
    def register_outputs(self):
        @self.output
        @render_widget
        def gulf_war_plot():
            return self.create_plot()