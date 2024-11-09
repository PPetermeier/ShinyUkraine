"""
Financial aid by type visualization card.
"""

import pandas as pd
import plotly.graph_objects as go
from config import COLOR_PALETTE
from server.database import load_data_from_table
from server.queries import FINANCIAL_AID_TABLE  # Add this import
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget


class FinancialByTypeCard:
    """UI components for the financial aid by type visualization card."""

    @staticmethod
    def ui():
        """Return the card UI elements."""
        return ui.card(
            ui.card_header(
                ui.h3("Financial Bilateral Allocations by Type"),
                ui.div(
                    {"class": "card-subtitle text-muted"},
                    "Includes bilateral financial commitments to Ukraine. Does not include private donations, "
                    "support for refugees outside of Ukraine, and aid by international organisations. "
                    "Commitments by EU Institutions include Commission and Council and EIB. "
                    "For information on data quality and transparency please see our data transparency index.",
                ),
            ),
            ui.layout_sidebar(
                ui.sidebar(
                    "Input options",
                    ui.input_checkbox_group(
                        "financial_types_select",
                        "Select Financial Aid Types",
                        choices={
                            "loan": "Loans",
                            "grant": "Grants",
                            "guarantee": "Guarantees",
                            "central_bank_swap_line": "Central Bank Swap Lines"
                        },
                        selected=["loan", "grant", "guarantee", "central_bank_swap_line"],
                    ),
                    ui.input_numeric("top_n_countries", "Show Top N Countries", value=15, min=5, max=50),
                    position="fixed",
                    min_width="300px",
                    max_width="300px",
                    bg="#f8f8f8",
                ),
                output_widget("financial_types_plot"),
            ),
            height="800px",
        )


class FinancialByTypeServer:
    """Server logic for the financial aid by type visualization card."""

    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
        self._filtered_data = reactive.Calc(self._compute_filtered_data)

    def _compute_filtered_data(self):
        """Internal method to compute filtered data based on user inputs."""
        # Construct the query based on selected columns
        selected_types = self.input.financial_types_select()
        
        # Build the SELECT clause with proper quoting for reserved keywords
        select_columns = ['country']
        for col in selected_types:
            select_columns.append(f'"{col}"')
        
        select_clause = ", ".join(select_columns)
        
        # Build the query
        query = f"""
            SELECT {select_clause}
            FROM {FINANCIAL_AID_TABLE}
            WHERE country IS NOT NULL
        """
        
        # Load data using the existing database utility
        df = load_data_from_table(table_name_or_query=query)
        
        # Calculate total aid for sorting
        df['total_aid'] = df.iloc[:, 1:].sum(axis=1)
        df = df.nlargest(self.input.top_n_countries(), 'total_aid')
        df = df.sort_values('total_aid', ascending=True)  # For bottom-to-top display
        
        return df

    def create_plot(self):
        """Create and return the plot figure."""
        data = self._filtered_data()
        if data.empty:
            return go.Figure()

        fig = go.Figure()

        # Color mapping using new color palette
        color_mapping = {
            'loan': COLOR_PALETTE['financial_loan'],
            'grant': COLOR_PALETTE['financial_grant'],
            'guarantee': COLOR_PALETTE['financial_guarantee'],
            'central_bank_swap_line': COLOR_PALETTE['financial_swap']
        }

        # Nice labels for the legend
        label_mapping = {
            'loan': 'Loan',
            'grant': 'Grant',
            'guarantee': 'Guarantee',
            'central_bank_swap_line': 'Central Bank Swap Line'
        }

        # Add bars for each type of aid
        for col in data.columns:
            if col not in ['country', 'total_aid']:
                fig.add_trace(go.Bar(
                    name=label_mapping.get(col, col),
                    y=data['country'],
                    x=data[col],
                    orientation='h',
                    marker_color=color_mapping.get(col, '#000000'),
                    hovertemplate="%{y}<br>" + 
                                "%{customdata}<br>" + 
                                "Value: %{x:.1f}B €<extra></extra>",
                    customdata=[label_mapping.get(col, col)] * len(data),
                ))

        fig.update_layout(
            title="Financial Bilateral Allocations by Type",
            xaxis_title="billion Euros",
            yaxis_title="",
            barmode='stack',
            template="plotly_white",
            height=600,
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(
                yanchor="bottom",
                y=0.01,
                xanchor="right",
                x=0.99,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.2)",
                borderwidth=1
            ),
            showlegend=True,
            hovermode="y unified",
            autosize=True,
            yaxis=dict(
                showgrid=False,
                gridcolor="rgba(0,0,0,0.1)",
                zerolinecolor="rgba(0,0,0,0.2)",
            ),
            xaxis=dict(
                showgrid=False,
                gridcolor="rgba(0,0,0,0.1)",
                zerolinecolor="rgba(0,0,0,0.2)",
                tickformat=".1f",
            ),
            plot_bgcolor="rgba(255,255,255,1)",
            paper_bgcolor="rgba(255,255,255,1)",
        )

        return fig

    def register_outputs(self):
        """Register all outputs for the module."""

        @self.output
        @render_widget
        def financial_types_plot():
            return self.create_plot()