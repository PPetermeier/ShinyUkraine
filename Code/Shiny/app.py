import pandas as pd
import duckdb
import seaborn as sns
import matplotlib.pyplot as plt
from shiny import ui, render, reactive, App
from shinywidgets import output_widget, render_widget
import plotly.express as px
from pathlib import Path
import plotly.graph_objects as go

# Define consistent colors for US and EU

COLOR_PALETTE = {
    "united_states": "#1E3D59",  # Deep navy blue
    "europe": "#FFC13B",  # Golden yellow
    "total": "#2ECC71",  # Emerald green for total
}


# Load data function
def load_data():
    conn = duckdb.connect("Data/ukrainesupporttracker.db")
    query = """
        SELECT month, 
               united_states_allocated__billion,
               europe_allocated__billion
        FROM 'c_allocated_over_time'
        ORDER BY month
    """
    df = conn.execute(query).fetchdf()
    conn.close()
    return df


# UI Definition

app_ui = ui.page_navbar(
    ui.nav_panel(
        "Over time",
        ui.page_fillable(
            ui.div(
                {"style": "display: flex; height: 100vh; overflow: hidden;"},
                ui.div(
                    {"style": "width: 300px; flex-shrink: 0; background-color: #f8f8f8; padding: 15px; overflow-y: auto;"},
                    "Input options",
                    ui.input_checkbox_group(
                        "regions", "Select Regions", choices={"united_states": "United States", "europe": "Europe"}, selected=["united_states", "europe"]
                    ),
                    ui.input_date_range("date_range", "Select Date Range", start="2022-02-01", end="2024-12-31", min="2022-02-01", max="2024-12-31"  ),
                    ui.input_switch("additive", "Show Cumulative View", value=False),
                ),
                ui.div(
                    {"style": "flex-grow: 1; padding: 15px; overflow-y: auto;"}, ui.card(ui.card_header("Support each month"), output_widget("support_plot"))
                ),
            )
        ),
    ),
    title="Ukraine Support Tracker in Shiny",
    id="timeseries",
)


def server(input, output, session):
    df = load_data()

    @reactive.Calc
    def filtered_data():
        selected_cols = [f"{region}_allocated__billion" for region in input.regions()]

        mask = (pd.to_datetime(df["month"]) >= pd.to_datetime(input.date_range()[0])) & (pd.to_datetime(df["month"]) <= pd.to_datetime(input.date_range()[1]))
        filtered_df = df[mask].copy()

        if not selected_cols:
            return pd.DataFrame()

        result = filtered_df[["month"] + selected_cols]

        if input.additive():
            for col in selected_cols:
                result[col] = result[col].cumsum()

            # Calculate total if both regions are selected
            if len(selected_cols) == 2:
                result["total"] = result[selected_cols].sum(axis=1)

        return result

    @output
    @render_widget
    def support_plot():
        data = filtered_data()
        if data.empty:
            return go.Figure()

        if input.additive():
            fig = go.Figure()

            # Get the maximum values to determine plotting order
            max_us = data["united_states_allocated__billion"].max() if "united_states_allocated__billion" in data.columns else 0
            max_eu = data["europe_allocated__billion"].max() if "europe_allocated__billion" in data.columns else 0

            # Plot the larger value first (in background)
            regions = sorted(input.regions(), key=lambda x: data[f"{x}_allocated__billion"].max(), reverse=True)

            for region in regions:
                col_name = f"{region}_allocated__billion"
                name = "United States" if region == "united_states" else "Europe"

                fig.add_trace(
                    go.Scatter(
                        x=data["month"],
                        y=data[col_name],
                        name=name,
                        fill="tozeroy",
                        mode="lines",
                        line=dict(color=COLOR_PALETTE[region], width=2),
                        fillcolor=COLOR_PALETTE[region],
                        opacity=0.85 if region == regions[-1] else 0.75,
                        hovertemplate="%{y:.1f}B $<extra></extra>",
                    )
                )

            # Add total line if both regions are selected
            if len(regions) == 2 and "total" in data.columns:
                fig.add_trace(
                    go.Scatter(
                        x=data["month"],
                        y=data["total"],
                        name="Total Support",
                        mode="lines",
                        line=dict(color=COLOR_PALETTE["total"], width=3, dash="solid"),
                        hovertemplate="Total: %{y:.1f}B $<extra></extra>",
                    )
                )

            title = "Cumulative Support Allocation Over Time"

        else:
            fig = go.Figure()

            for region in input.regions():
                col_name = f"{region}_allocated__billion"
                fig.add_trace(
                    go.Bar(
                        x=data["month"], y=data[col_name], name="United States" if region == "united_states" else "Europe", marker_color=COLOR_PALETTE[region]
                    )
                )

            # Add total bars if both regions are selected
            if len(input.regions()) == 2:
                total = data[[f"{region}_allocated__billion" for region in input.regions()]].sum(axis=1)
                fig.add_trace(
                    go.Scatter(
                        x=data["month"],
                        y=total,
                        name="Total Support",
                        mode="lines+markers",
                        line=dict(color=COLOR_PALETTE["total"], width=3),
                        marker=dict(size=8),
                        hovertemplate="Total: %{y:.1f}B $<extra></extra>",
                    )
                )

            title = "Monthly Support Allocation"

        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title="Month",
            yaxis_title="Allocated Support (Billion $)",
            barmode="group",
            template="plotly_white",
            height=600,
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            showlegend=True,
            hovermode="x unified",
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


app = App(app_ui, server)
