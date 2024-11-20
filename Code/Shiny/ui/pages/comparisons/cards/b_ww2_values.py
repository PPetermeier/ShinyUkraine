import plotly.graph_objects as go
from shiny import reactive, ui
from shinywidgets import output_widget, render_widget

from server import load_data_from_table
from server.queries import WW2_COMPARISON_QUERY
from config import LAST_UPDATE, COMPARISONS_MARGIN, COLOR_PALETTE


class WW2UkraineComparisonCard:
    @staticmethod
    def ui():
        return ui.card(
            ui.card_header(
                ui.div(
                    {"class": "d-flex justify-content-between align-items-center"},
                    ui.div(
                        {"class": "flex-grow-1"},
                        ui.h3("Historical Military Support Comparison"),
                        ui.div({"class": "card-subtitle text-muted"}, "WW2 Lend-Lease vs Current Ukraine Support"),
                    ),
                    ui.div({"class": "ms-3"}, ui.input_switch("show_absolute_ww2_values", "Show Absolute Values", value=False)),
                ),
            ),
            output_widget("support_comparison_plot"),
        )


class WW2UkraineComparisonServer:
    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
        self.comparison_data = load_data_from_table(WW2_COMPARISON_QUERY)

        self.color_map = {
            "WW2 US to UK": COLOR_PALETTE.get("WW2 US UK"),
            "WW2 US to USSR": COLOR_PALETTE.get("WW2 US UDSSR"),
            "WW2 British to USSR": COLOR_PALETTE.get("WW2 UK UDSSR"),
            "WW2 US to France": COLOR_PALETTE.get("WW2 US France"),
            "British to Ukraine": COLOR_PALETTE.get("UK Ukraine"),
            "US to Ukraine": COLOR_PALETTE.get("US Ukraine"),
        }

    def create_plot(self):
            df = self.comparison_data.copy()
            show_absolute_ww2_values = self.input.show_absolute_ww2_values()

            sort_column = "absolute_value" if show_absolute_ww2_values else "gdp_share"
            df = df.sort_values(by=sort_column, ascending=True)

            # Create mapping between original names and legend names
            df["legend_name"] = df["military_support"].apply(
                lambda x: "WW2 US to UK"
                if "US support to UK" in x
                else "WW2 US to USSR"
                if "US support to USSR" in x
                else "WW2 British to USSR"
                if "British support to USSR" in x
                else "WW2 US to France"
                if "US support to France" in x
                else "British to Ukraine"
                if "British military aid to Ukraine" in x
                else "US to Ukraine"
            )

            fig = go.Figure()

            # Create traces for all possible legend entries
            for legend_name in self.color_map.keys():
                mask = df["legend_name"] == legend_name
                if not mask.any():
                    continue

                data = df[mask]
                # Create empty arrays for all positions
                x_values = [None] * len(df)
                text_values = [None] * len(df)
                customdata = [[None, None, None]] * len(df)

                # Fill in values only for this trace's positions
                for idx, (_, row) in enumerate(df.iterrows()):
                    if row["legend_name"] == legend_name:
                        value = row["absolute_value"] if show_absolute_ww2_values else row["gdp_share"]
                        x_values[idx] = value
                        text_values[idx] = f"{value:,.2f}{' €B' if show_absolute_ww2_values else '%'}"
                        customdata[idx] = [row["gdp_share"], row["absolute_value"], row["military_conflict"]]

                fig.add_trace(
                    go.Bar(
                        x=x_values,
                        y=df["military_support"],
                        orientation="h",
                        name=legend_name,
                        marker_color=COLOR_PALETTE[legend_name],
                        text=text_values,
                        textposition="auto",
                        customdata=customdata,
                        hovertemplate=(
                            "%{y}<br>" +
                            "GDP Share: %{customdata[0]:.2f}%<br>" +
                            "Amount: %{customdata[1]:.2f}€B<br>" +
                            "Conflict: %{customdata[2]}"
                        ),
                    )
                )

            fig.update_layout(
                height=700,
                margin=COMPARISONS_MARGIN,
                xaxis_title="Billion 2022 Euros" if show_absolute_ww2_values else "% of donor GDP",
                template="plotly_white",
                title=dict(
                    text=(
                        "Historical Military Support Comparison<br>"
                        f"<span style='font-size: 12px; color: gray;'>"
                        "This figure compares military support across major conflicts, "
                        "showing both WW2 Lend-Lease and current Ukraine support."
                        f"<br>Last updated: {LAST_UPDATE}, Sheet: Fig 16</span>"
                    ),
                    x=0.5,
                    y=0.98,
                    xanchor="center",
                    yanchor="top",
                    font=dict(size=16),
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
                ),
                showlegend=True,
                xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.1)", zeroline=True, zerolinecolor="rgba(0,0,0,0.2)"),
                yaxis=dict(showticklabels=False, showgrid=False),
                barmode="overlay",
                autosize=True,
                hovermode="y unified",  # Added unified hover mode
            )

            return fig

    def register_outputs(self):
        @self.output
        @render_widget
        def support_comparison_plot():
            return self.create_plot()
