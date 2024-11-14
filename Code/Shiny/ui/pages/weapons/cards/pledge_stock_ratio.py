from shiny import ui, reactive
from shinywidgets import output_widget, render_widget
import plotly.graph_objects as go
from server.database import load_data_from_table
from server.queries import WEAPON_STOCK_PLEDGES_QUERY
from config import COLOR_PALETTE, MARGIN, LAST_UPDATE
from ui.colorutilities import desaturate_color

class PledgeStockCard:
    """UI components for the weapons stock pledges visualization card."""
    
    @staticmethod
    def ui():
        return ui.card(
            ui.card_header(
                ui.div(
                    {"class": "d-flex justify-content-between align-items-center"},
                    ui.div(
                        {"class": "flex-grow-1"},
                        ui.h3("Military Aid as Share of National Stocks"),
                        ui.div(
                            {"class": "card-subtitle text-muted"},
                            "Average share of heavy weapon stocks (tanks, howitzers, MLRS) pledged and delivered to Ukraine",
                        ),
                    ),
                    ui.div(
                        {"class": "ms-3 d-flex align-items-center"},
                        ui.span({"class": "me-2"}, "Top"),
                        ui.input_numeric(
                            "numeric_pledge_stocks",
                            None,  # No label needed as it's inline
                            value=19,
                            min=5,
                            max=30,
                            width="80px",
                        ),
                        ui.span({"class": "ms-2"}, "countries"),
                    ),
                ),
            ),
            output_widget("pledges_weapon_types_plot"),
            height="800px",
        )

class PledgeStockServer:
    """Server logic for the weapons stock pledges visualization card."""
    
    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
        self._filtered_data = reactive.Calc(self._compute_filtered_data)
    
    def _compute_filtered_data(self):
        """Process data for visualization."""
        # Load the full dataset
        df = load_data_from_table(table_name_or_query=WEAPON_STOCK_PLEDGES_QUERY)
        
        # Calculate total pledged (delivered + to_be_delivered) for sorting
        df['total_pledged'] = df['delivered'].fillna(0) + df['to_be_delivered'].fillna(0)
        
        # Get top N countries based on total pledged
        df = df.nlargest(self.input.numeric_pledge_stocks(), 'total_pledged')
        
        # Sort by total pledged for display
        
        return df
    
    def create_plot(self):
            """Create the stacked bar plot visualization."""
            data = self._filtered_data()
            
            if data.empty:
                return go.Figure()
                
            fig = go.Figure()
            
            # Create traces with consistent colors for all countries
            fig.add_trace(go.Bar(
                y=data['country'],
                x=data['delivered'].multiply(100),
                name='Delivered',
                orientation='h',
                marker_color=COLOR_PALETTE.get("military"),
                hovertemplate="Delivered: %{x:.1f}%<extra></extra>"
            ))
            
            fig.add_trace(go.Bar(
                y=data['country'],
                x=data['to_be_delivered'].multiply(100),
                name='To Be Delivered',
                orientation='h',
                marker_color=COLOR_PALETTE.get("aid_committed"),
                hovertemplate="To Be Delivered: %{x:.1f}%<extra></extra>"
            ))
            
            # Dynamic height calculation
            plot_height = max(600, len(data) * 40)
            
            fig.update_layout(
                title=dict(
                    text=f"Share of National Stocks Pledged to Ukraine<br><sub>Last updated: {LAST_UPDATE}, Sheet: Fig 14</sub>",
                    font=dict(size=14),
                    y=0.95,
                    x=0.5,
                    xanchor="center",
                    yanchor="top"
                ),
                height=plot_height,
                margin=MARGIN,
                barmode='stack',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                xaxis=dict(
                    title="Percentage of National Stock",
                    ticksuffix="%",
                    showgrid=True,
                    gridcolor="rgba(0,0,0,0.1)",
                ),
                yaxis=dict(
                    title=None,
                    autorange="reversed",
                    showgrid=False,
                    gridcolor="rgba(0,0,0,0.1)",
                    zerolinecolor="rgba(0,0,0,0.2)",
                    categoryorder='total descending'
                ),
                plot_bgcolor="rgba(255,255,255,1)",
                paper_bgcolor="rgba(255,255,255,1)",
            )
            
            return fig
    
    def register_outputs(self):
        """Register all outputs for the module."""
        
        @self.output
        @render_widget
        def pledges_weapon_types_plot():
            return self.create_plot()