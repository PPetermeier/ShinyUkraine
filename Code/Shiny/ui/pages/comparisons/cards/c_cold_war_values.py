import plotly.graph_objects as go
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget

from server import load_data_from_table
from server.queries import US_WARS_COMPARISON_QUERY
from config import LAST_UPDATE, COMPARISONS_MARGIN, COLOR_PALETTE 

class ColdWarCard:
    @staticmethod
    def ui():
        return ui.card(
            ui.card_header(
                ui.div(
                    {"class": "d-flex justify-content-between align-items-center"},
                    ui.div(
                        {"class": "flex-grow-1"},
                        ui.h3("US Military Support Comparison"),
                        ui.div(
                            {"class": "card-subtitle text-muted mb-4"},
                            "Historical US Military Expenditure vs Ukraine Support"
                        ),
                    ),
                    ui.div(
                        {"class": "ms-3"},
                        ui.input_switch("show_absolute_values", "Show Absolute Values", value=False)
                    ),
                ),
            ),
            output_widget("military_expenditure_plot", height="auto") 
        )

class ColdWarServer:
    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
        self.expenditure_data = load_data_from_table(US_WARS_COMPARISON_QUERY)
        
    def create_plot(self):
        show_absolute_values = self.input.show_absolute_values()
        df = self.expenditure_data.sort_values(
            by='gdp_share' if not show_absolute_values else 'absolute_value',
            ascending=True
        )
        
        fig = go.Figure()
        
        # Create one trace per conflict for interactive legend
        for _, row in df.iterrows():
            conflict_name = row['military_support']
            legend_name = conflict_name.split('(')[0].strip()
            
            fig.add_trace(
                go.Bar(
                    x=[row['absolute_value'] if show_absolute_values else row['gdp_share']],
                    y=[conflict_name],
                    orientation='h',
                    name=legend_name,
                    marker_color=COLOR_PALETTE[conflict_name],
                    text=[f"{row['absolute_value']:,.2f} €B" if show_absolute_values 
                          else f"{row['gdp_share']:,.2f}%"],
                    textposition='auto',
                    customdata=[[
                        row['gdp_share'],
                        row['absolute_value']
                    ]],
                    hovertemplate=(
                        "%{y}<br>" +
                        "GDP Share: %{customdata[0]:.2f}%<br>" +
                        "Amount: %{customdata[1]:.2f}€B"
                    ),
                )
            )
                
        fig.update_layout(
            height=700,
            margin=COMPARISONS_MARGIN,
            xaxis_title="Billion 2021 Euros" if show_absolute_values else "% of US GDP",
            template="plotly_white",
            title=dict(
                text=(
                    "US Military Support Comparison<br>"
                    f"<span style='font-size: 12px; color: gray;'>"
                    "This figure compares US military expenditure across major conflicts "
                    "with current Ukraine support."
                    f"<br>Last updated: {LAST_UPDATE}, Sheet: Fig 17</span>"
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
                showgrid=True,
                gridcolor="rgba(0,0,0,0.1)",
                zeroline=True,
                zerolinecolor="rgba(0,0,0,0.2)"
            ),
            yaxis=dict(
                showticklabels=False,
                showgrid=False
            ),
            barmode='overlay',
            autosize=True,
            hovermode="y unified",  # Added unified hover mode
        )
        
        return fig
    
    def register_outputs(self):
        @self.output
        @render_widget
        def military_expenditure_plot():
            return self.create_plot()