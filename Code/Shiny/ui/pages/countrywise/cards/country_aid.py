"""
Country and aid type visualization card.
"""

import pandas as pd
import plotly.graph_objects as go
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget
from config import COLOR_PALETTE
from server import load_country_data, COUNTRY_AID_COLUMNS

class CountryAidCard:
    """UI components for the country aid visualization card."""

    @staticmethod
    def ui():
        """Return the card UI elements."""
        return ui.card(
            ui.card_header(
                ui.h3("Aid by country and type"), 
                ui.div({"class": "card-subtitle text-muted"}, "Includes bilateral allocations to Ukraine and cost estimates for refugees in donor countries. Allocations are defined as aid which has been delivered or specified for delivery. Does not include private donations, support for refugees outside of Ukraine, and aid by international organizations. Data on European Union aid include the EU Commission and Council, EPF, and EIB. For information on data quality and transparency please see our data transparency index.")
            ),
            ui.layout_sidebar(
                ui.sidebar(
                    "Input options",
                    ui.input_checkbox_group(
                        "aid_types",
                        "Select Aid Types",
                        choices={
                            "financial": "Financial",
                            "humanitarian": "Humanitarian",
                            "military": "Military",
                            "refugee_cost_estimation": "Refugee Support"
                        },
                        selected=["financial", "military"],
                    ),
                    ui.input_numeric(
                        "top_n_countries",
                        "Show Top N Countries",
                        value=15,
                        min=5,
                        max=50
                    ),
                    position="fixed",
                    min_width="300px",
                    max_width="300px",
                    bg="#f8f8f8",
                ),
                output_widget("country_aid_plot"),
            ),
            height="800px",
        )


class CountryAidServer:
    """Server logic for the country aid visualization card."""
    
    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
        self.df = load_country_data()
        self._filtered_data = reactive.Calc(self._compute_filtered_data)
        self.register_outputs()

    def _compute_filtered_data(self):
        """Filter and process data based on user selections."""
        selected_cols = self.input.aid_types()
        
        if not selected_cols:
            return pd.DataFrame()
            
        # Filter data for selected aid types
        result = self.df.copy()
        
        # Calculate total aid for sorting - fix: iterate through columns
        total_aid = pd.Series(0, index=result.index)
        for col in selected_cols:
            if col in result.columns:  # Add safety check
                total_aid += result[col]
        
        result['total_aid'] = total_aid
        
        # Get top N countries and sort
        result = result.nlargest(self.input.top_n_countries(), 'total_aid')
        result = result.sort_values('total_aid', ascending=True)
        
        # Return only needed columns
        return result[['country'] + list(selected_cols)]

    def create_plot(self):
        """Create and return the plot figure."""
        data = self._filtered_data()
        
        if data.empty:
            return go.Figure()

        fig = go.Figure()

        # Color mapping for aid types
        colors = {
            "financial": COLOR_PALETTE.get("financial"),
            "humanitarian": COLOR_PALETTE.get("humanitarian"),
            "military": COLOR_PALETTE.get("military"),
            "refugee_cost_estimation": COLOR_PALETTE.get("refugee")
        }

        # Name mapping for aid types
        name_map = {
            "financial": "Financial",
            "humanitarian": "Humanitarian",
            "military": "Military",
            "refugee_cost_estimation": "Refugee Support"
        }

        # Add bars for each selected aid type
        for aid_type in self.input.aid_types():
            fig.add_trace(
                go.Bar(
                    y=data['country'],
                    x=data[aid_type],
                    name=name_map[aid_type],
                    orientation='h',
                    marker_color=colors[aid_type],
                )
            )

        fig.update_layout(
            title="Aid Allocation by Country and Type",
            xaxis_title="Aid Amount (Billion €)",
            yaxis_title="Country",
            barmode='stack',
            template="plotly_white",
            height=600,
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(
                yanchor="bottom",  # Anchor to bottom
                y=0.01,           # Position near bottom
                xanchor="right",  # Anchor to right
                x=0.99,          # Position near right
                bgcolor="rgba(255, 255, 255, 0.8)",  # Semi-transparent white background
                bordercolor="rgba(0, 0, 0, 0.2)",    # Light border
                borderwidth=1
            ),
            showlegend=True,
            hovermode="y unified",
            autosize=True,
            yaxis=dict(
                gridcolor="rgba(0,0,0,0.1)",
                zerolinecolor="rgba(0,0,0,0.2)",
            ),
            xaxis=dict(
                gridcolor="rgba(0,0,0,0.1)",
                zerolinecolor="rgba(0,0,0,0.2)",
            ),
            plot_bgcolor="rgba(255,255,255,1)",
            paper_bgcolor="rgba(255,255,255,1)",
        )

        return fig

    def register_outputs(self):
        """Register all outputs for the module."""
        
        @self.output
        @render_widget
        def country_aid_plot():
            return self.create_plot()