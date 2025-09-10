import dash
from dash import dcc, html, Input, Output, register_page
import plotly.express as px
import pandas as pd
import numpy as np

# Register page
register_page(__name__, path="/page3", name="Extreme Weather")

# Define regions
regions_info = {
    "Virginia Beach": {"lat": 36.85, "lon": -75.98, "population": 450000},
    "Arlington": {"lat": 38.88, "lon": -77.10, "population": 240000},
    "Richmond": {"lat": 37.54, "lon": -77.43, "population": 230000},
    "Norfolk": {"lat": 36.85, "lon": -76.29, "population": 245000},
}

region_colors = ["#113E14", "#1A5B07", "#2C5C99", "#99B7F0"]

# Generate sample data
all_years = range(2020, 2026)
data = []
for year in all_years:
    year_dates = pd.date_range(f"{year}-01-01", f"{year}-12-31")
    for region, info in regions_info.items():
        for date in year_dates:
            data.append({
                "Date": date,
                "Year": year,
                "Month": date.month,
                "Region": region,
                "MaxTemp": np.random.randint(35, 45),
                "HeatCases": np.random.randint(5, 50),
                "Population": info["population"],
                "Latitude": info["lat"],
                "Longitude": info["lon"]
            })

df = pd.DataFrame(data)

# Layout
layout = html.Div([
    html.H1("Extreme Heat & Public Health",
            style={'textAlign': 'center', 'marginBottom': '30px'}),

    html.Div([
        # Sidebar
        html.Div([
            html.H3("Filter Regions & Year"),
            html.Hr(),

            html.Label("Regions:"),
            dcc.Checklist(
                id='region-checklist',
                options=[{"label": r, "value": r} for r in regions_info.keys()],
                value=list(regions_info.keys()),
                labelStyle={'display': 'block', 'marginBottom': '5px', 'color': 'white'}
            ),

            html.Label("Year:"),
            dcc.Slider(
                id='year-slider',
                min=2020,
                max=2025,
                step=1,
                marks={year: str(year) for year in all_years},
                value=2025
            ),
        ], className="page3-sidebar"),

        # Content
        html.Div([
            html.Div(id='kpi-container', className="page3-kpi"),

            html.Div([
                dcc.Graph(id='health-bar-chart', style={'width': '80%', 'display': 'inline-block'}),

                html.Div([
                    html.Label("Select Months:", style={'color': 'white', 'fontWeight': 'bold'}),
                    dcc.Checklist(
                        id='month-checklist',
                        options=[{"label": pd.to_datetime(f"2020-{m}-01").strftime("%B"), "value": m} for m in range(1, 13)],
                        value=[6],  # default June
                        labelStyle={'display': 'flex', 'alignItems': 'center', 'color': 'white', 'marginBottom': '5px'}
                    )
                ], style={'width': '18%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '2%'})
            ]),

            html.Div(
                dcc.Graph(id='heat-map'),
                className="map-box"
            )
        ], className="page3-content")
    ])
], className="page3-container")


# Callback
@dash.callback(
    [Output('health-bar-chart', 'figure'),
     Output('heat-map', 'figure'),
     Output('kpi-container', 'children')],
    [Input('region-checklist', 'value'),
     Input('year-slider', 'value'),
     Input('month-checklist', 'value')]
)
def update_dashboard(selected_regions, selected_year, selected_months):
    if not selected_months:
        return px.scatter(), px.scatter(), []

    filtered_df = df[
        (df['Year'] == selected_year) &
        (df['Month'].isin(selected_months)) &
        (df['Region'].isin(selected_regions))
    ]

    if filtered_df.empty:
        return px.scatter(), px.scatter(), []

    # Aggregate data by Region and Month
    month_region_df = filtered_df.groupby(['Month', 'Region'], as_index=False).agg({
        'HeatCases': 'sum',
        'MaxTemp': 'mean'
    })
    month_region_df['MonthName'] = month_region_df['Month'].apply(lambda m: pd.to_datetime(f"2020-{m}-01").strftime("%B"))

    # Bar chart: x = month, y = HeatCases, color = Region
    health_fig = px.bar(
        month_region_df,
        x='MonthName',
        y='HeatCases',
        color='Region',
        barmode='group',
        title=f'Heat-Related Cases ({selected_year})',
        color_discrete_sequence=region_colors
    )
    health_fig.update_layout(title_x=0.5, font=dict(size=14), legend_title='Region')

    # Map: show city positions
    city_df = filtered_df.groupby('Region', as_index=False).agg({
        'HeatCases': 'sum',
        'MaxTemp': 'mean',
        'Population': 'first',
        'Latitude': 'first',
        'Longitude': 'first'
    })
    map_fig = px.scatter_mapbox(
        city_df,
        lat="Latitude",
        lon="Longitude",
        size="Population",
        color="Region",
        hover_name="Region",
        hover_data={"MaxTemp": True, "HeatCases": True, "Population": True},
        size_max=50,
        zoom=6,
        color_discrete_sequence=region_colors
    )
    map_fig.update_layout(mapbox_style="open-street-map",
                          margin={"r": 0, "t": 0, "l": 0, "b": 0})

    # KPIs
    avg_temp = round(filtered_df['MaxTemp'].mean(), 1)
    total_cases = filtered_df['HeatCases'].sum()
    high_temp_days = (filtered_df['MaxTemp'] >= 40).sum()

    kpis = [
        html.Div([
            html.H4("Avg Temp"),
            html.P(f"{avg_temp} °C")
        ]),
        html.Div([
            html.H4("Total Heat Cases"),
            html.P(f"{total_cases}")
        ]),
        html.Div([
            html.H4("Days ≥ 40°C"),
            html.P(f"{high_temp_days}")
        ]),
    ]

    return health_fig, map_fig, kpis
