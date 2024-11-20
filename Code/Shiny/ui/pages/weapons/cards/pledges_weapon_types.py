from shiny import ui, reactive
from shinywidgets import output_widget, render_widget
import plotly.graph_objects as go
import pandas as pd
from server.database import load_data_from_table
from server.queries import WEAPON_TYPE_PLEDGES_QUERY
from config import COLOR_PALETTE, COMPARISONS_MARGIN, LAST_UPDATE


class WeaponTypeCard:
    """Base class for individual weapon type cards."""
    
    def __init__(self, title, weapon_type, delivered_col, to_deliver_col):
        self.title = title
        self.weapon_type = weapon_type
        self.delivered_col = delivered_col
        self.to_deliver_col = to_deliver_col

    def ui(self):
        return ui.card(
            ui.div(
                output_widget(f"weapon_type_{self.weapon_type}_plot"),
            ),
            {"class": "mb-4", "style":"height: 800px;"}  # Add margin bottom for spacing between cards
        )


class WeaponTypeServer:
    """Server logic for individual weapon type plots."""

    def __init__(self, input, output, session, weapon_type, delivered_col, to_deliver_col, title):
        self.input = input
        self.output = output
        self.session = session
        self.weapon_type = weapon_type
        self.delivered_col = delivered_col
        self.to_deliver_col = to_deliver_col
        self.title = title
        self._filtered_data = reactive.Calc(self._compute_filtered_data)

    def _compute_filtered_data(self):
        """Process data for visualization."""
        data = load_data_from_table(table_name_or_query=WEAPON_TYPE_PLEDGES_QUERY)
        
        weapon_data = data[["country", self.delivered_col, self.to_deliver_col]].copy()
        weapon_data = weapon_data[weapon_data[self.delivered_col].notna() | weapon_data[self.to_deliver_col].notna()]
        
        weapon_data["total"] = weapon_data[self.delivered_col].fillna(0) + weapon_data[self.to_deliver_col].fillna(0)
        weapon_data = weapon_data.sort_values("total", ascending=False)
        
        mask = weapon_data[self.delivered_col] > 0
        delivered_countries = weapon_data[mask]
        if not weapon_data[~mask].empty:
            zero_delivery = weapon_data[~mask].iloc[0:1]
            weapon_data = pd.concat([delivered_countries, zero_delivery])
        
        return weapon_data


    def create_plot(self):
        data = self._filtered_data()
        
        if data.empty:
            return go.Figure()

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                y=data["country"],
                x=data[self.delivered_col].multiply(100),
                name="Pledged",
                orientation="h",
                marker_color=COLOR_PALETTE["military"],
                hovertemplate="Pledged: %{x:.1f}%",  # Simplified for unified hover
                text=[f"{v:.1f}" if v > 0 else "" for v in data[self.delivered_col].multiply(100)],
                textposition="inside",
                textfont=dict(color="white"),
                insidetextanchor="middle",
            )
        )

        plot_height = 600

        fig.update_layout(
            height=plot_height,
            margin=COMPARISONS_MARGIN,
            barmode="stack",
            showlegend=True,
            hovermode="y unified",  # Added unified hover mode
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.3,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(255,255,255,0)",
                bordercolor="rgba(255,255,255,0)"
            ),
            title=dict(
                text=f"{self.title}, pledged by donor country<br><sub>Last updated: {LAST_UPDATE}, Sheet: Fig 14</sub>",
                y=0.95,
                x=0.5,
                xanchor='center',
                yanchor='top',
                font=dict(size=14)
            ),
            plot_bgcolor="rgba(255,255,255,1)",
            paper_bgcolor="rgba(255,255,255,1)",
        )

        fig.update_xaxes(
            title="Share of National Stock (%)",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.1)",
            ticksuffix="%"
        )
        
        fig.update_yaxes(
            autorange="reversed",
            showgrid=False,
            gridcolor="rgba(0,0,0,0.1)",
            zerolinecolor="rgba(0,0,0,0.2)",
            categoryorder="total descending",
        )

        return fig
    
    def register_outputs(self):
        """Register outputs for the weapon type."""
        
        @self.output(id=f"weapon_type_{self.weapon_type}_plot")
        @render_widget
        def _():
            return self.create_plot()


class WeaponTypesCard:
    """Main container for all weapon type cards."""

    @staticmethod
    def ui():
        return ui.div(
            WeaponTypeCard("Tanks", "tanks", "tanks_delivered", "tanks_to_deliver").ui(),
            WeaponTypeCard("Howitzers", "howitzers", "howitzers_delivered", "howitzers_to_deliver").ui(),
            WeaponTypeCard("MLRS", "mlrs", "mlrs_delivered", "mlrs_to_deliver").ui(),
        )



class WeaponTypesServer:
    """Server logic for all weapon type cards."""

    def __init__(self, input, output, session):
        self.tanks_server = WeaponTypeServer(input, output, session, "tanks", "tanks_delivered", "tanks_to_deliver", "Tanks")
        self.howitzers_server = WeaponTypeServer(input, output, session, "howitzers", "howitzers_delivered", "howitzers_to_deliver", "Howitzers (155/152mm)")
        self.mlrs_server = WeaponTypeServer(input, output, session, "mlrs", "mlrs_delivered", "mlrs_to_deliver", "Multiple Launch Rocket Systems")

    def register_outputs(self):
        """Register all outputs for all weapon types."""
        self.tanks_server.register_outputs()
        self.howitzers_server.register_outputs()
        self.mlrs_server.register_outputs()