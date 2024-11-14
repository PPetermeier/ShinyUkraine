import plotly.graph_objects as go
from plotly.subplots import make_subplots
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget 

from ....colorutilities import desaturate_color
from config import COLOR_PALETTE, LAST_UPDATE, MARGIN
from server import load_data_from_table, WW2_WEAPON_CATEGORIES, WW2_EQUIPMENT_CATEGORIZED_QUERY, WW2_CONFLICTS

class WW2EquipmentComparisonCard:
    """UI components for the WW2 equipment comparison visualization card."""

    @staticmethod
    def ui():
        """Return the card UI elements."""
        return ui.card(
            ui.card_header(
                ui.div(
                    {"class": "d-flex justify-content-between align-items-center"},
                    ui.div(
                        {"class": "flex-grow-1"},
                        ui.h3("Historical Military Support Comparison"),
                        ui.div(
                            {"class": "card-subtitle text-muted"},
                            "Comparing military equipment support across major conflicts"
                        ),
                    ),
                    ui.div(
                        {"class": "ms-3"},
                        ui.input_switch("show_absolute", "Show Absolute Numbers", value=False)
                    ),
                ),
            ),
            output_widget("equipment_comparison_plot"),
        )
class WW2EquipmentComparisonServer:
    """Server logic for the WW2 equipment comparison visualization."""

    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session

    def _compute_filtered_data(self):
        """Process and filter data based on user selections."""
        conflicts_str = ", ".join(f"'{conflict}'" for conflict in WW2_CONFLICTS)
        query = WW2_EQUIPMENT_CATEGORIZED_QUERY.format(conflicts=conflicts_str)
        df = load_data_from_table(table_name_or_query=query)
        
        # Calculate normalized values by category if needed
        if not self.input.show_absolute():
            for category in df['category'].unique():
                mask = df['category'] == category
                max_delivered = df.loc[mask, 'delivered'].max()
                if max_delivered > 0:
                    df.loc[mask, 'delivered_pct'] = df.loc[mask, 'delivered'] / max_delivered * 100
                    df.loc[mask, 'to_be_delivered_pct'] = df.loc[mask, 'to_be_delivered'] / max_delivered * 100
                
        return df
    
    def create_plot(self):
        """Create the comparison plot with three subplots."""
        try:
            data = self._compute_filtered_data()
            
            if data.empty:
                return go.Figure()

            # Create subplot figure
            fig = make_subplots(
                rows=1, cols=3,
                horizontal_spacing=0.05
            )

            color_map = {
                "WW2 lend-lease US total delivered": "#1f77b4",  # Blue
                "US to Great Britain (1941-45)": "#d62728",      # Red
                "US to USSR (1941-45)": "#2ca02c",              # Green
                "Spain (1936-39) Nationalists": "#ff7f0e",      # Orange
                "Spain (1936-39) Republicans": "#9467bd",       # Purple
                "Total supply to Ukraine": "#E31A1C"            # Bright red - high contrast color
            }

            # Category to subplot mapping
            category_cols = {
                'heavy': 1,
                'artillery': 2,
                'air': 3
            }

            for category, col in category_cols.items():
                category_data = data[data['category'] == category].copy()
                
                if not category_data.empty:
                    # Sort by total amount for consistent ordering
                    category_data['total'] = category_data['delivered'] + category_data['to_be_delivered']
                    category_data = category_data.sort_values('total', ascending=True)

                    for conflict in category_data['military_conflict'].unique():
                        conflict_data = category_data[category_data['military_conflict'] == conflict]
                        
                        # Determine values based on view type
                        if self.input.show_absolute():
                            delivered = conflict_data['delivered']
                            to_deliver = conflict_data['to_be_delivered']
                            value_suffix = " units"
                        else:
                            delivered = conflict_data['delivered_pct']
                            to_deliver = conflict_data['to_be_delivered_pct']
                            value_suffix = "%"

                        # Add delivered amounts
                        fig.add_trace(
                            go.Bar(
                                name=conflict,
                                y=[conflict],
                                x=delivered,
                                orientation='h',
                                marker_color=color_map.get(conflict),
                                legendgroup=conflict,
                                showlegend=(col == 1),  # Show legend only for first subplot
                                customdata=conflict_data[['delivered', 'to_be_delivered']],
                                hovertemplate=(
                                    f"<b>{conflict}</b><br>" +
                                    f"Delivered: %{{customdata[0]:,.0f}} units<br>" +
                                    f"To be delivered: %{{customdata[1]:,.0f}} units<br>" +
                                    f"Value: %{{x:.1f}}{value_suffix}<extra></extra>"
                                ),
                            ),
                            row=1, col=col
                        )

                        # Add to-be-delivered amounts if they exist
                        if conflict_data['to_be_delivered'].iloc[0] > 0:
                            fig.add_trace(
                                go.Bar(
                                    name=f"{conflict} (Planned)",
                                    y=[conflict],
                                    x=to_deliver,
                                    orientation='h',
                                    marker_color=desaturate_color(color_map.get(conflict)),
                                    legendgroup=conflict,
                                    showlegend=False,
                                    base=delivered,  # Stack on top of delivered
                                    customdata=conflict_data[['to_be_delivered']],
                                    hovertemplate=(
                                        f"<b>{conflict}</b><br>" +
                                        f"To be delivered: %{{customdata[0]:,.0f}} units<br>" +
                                        f"Value: %{{x:.1f}}{value_suffix}<extra></extra>"
                                    ),
                                ),
                                row=1, col=col
                            )

            # Update layout
                fig.update_layout(
                height=700,
                margin=dict(t=180, l=50, r=50, b=50),
                barmode='stack',
                template="plotly_white",
                title=dict(
                    text=(
                        "Historical Military Support Comparison<br>"
                        f"<span style='font-size: 12px; color: gray;'>"
                        "This figure compares the scale of military equipment support across major historical conflicts. "
                        "Data shows both delivered and planned equipment transfers."
                        f"<br>Last updated: {LAST_UPDATE}</span>"
                    ),
                    x=0.5,
                    y=0.98,
                    xanchor='center',
                    yanchor='top',
                    font=dict(size=16)
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.12,  # Moved legend up (closer to title)
                    xanchor="center",
                    x=0.5,
                    bgcolor="rgba(255, 255, 255, 0.8)",
                    bordercolor="rgba(0, 0, 0, 0.2)",
                    borderwidth=1
                ),
                showlegend=True,
            )

            # Add category labels at the top of each subplot
            annotations = [
                dict(
                    text="Heavy Equipment (Tanks)", 
                    x=0.16, 
                    y=1.08,
                    showarrow=False, 
                    xref="paper", 
                    yref="paper",
                    font=dict(size=14, weight='bold')
                ),
                dict(
                    text="Artillery Systems", 
                    x=0.5, 
                    y=1.08,
                    showarrow=False, 
                    xref="paper", 
                    yref="paper",
                    font=dict(size=14, weight='bold')
                ),
                dict(
                    text="Combat Aircraft", 
                    x=0.84, 
                    y=1.08,
                    showarrow=False, 
                    xref="paper", 
                    yref="paper",
                    font=dict(size=14, weight='bold')
                )
            ]
            fig.update_layout(annotations=annotations)

            # Update all subplot axes
            for i in range(1, 4):
                fig.update_xaxes(
                    title=("% of greatest value" if not self.input.show_absolute() else "Number of Units"),  # Updated x-axis label
                    showgrid=True,
                    gridcolor="rgba(0,0,0,0.1)",
                    zeroline=True,
                    zerolinecolor="rgba(0,0,0,0.2)",
                    row=1, col=i
                )
                fig.update_yaxes(
                    showgrid=False,
                    title="",
                    showticklabels=False,  # Hide y-axis tick labels
                    row=1, col=i
                )

            return fig
            
        except Exception as e:
            print(f"Error in create_plot: {str(e)}")
            fig = go.Figure()
            fig.add_annotation(text=f"Error: {str(e)}", 
                             xref="paper", yref="paper", 
                             x=0.5, y=0.5, showarrow=False)
            return fig
        

    def register_outputs(self):
        """Register all outputs for the module."""

        @self.output
        @render_widget
        def equipment_comparison_plot():
            return self.create_plot()