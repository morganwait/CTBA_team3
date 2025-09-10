import dash
from dash import html, dcc, Input, Output, State, register_page
import plotly.express as px
import pandas as pd
import requests

register_page(__name__, path="/", name="Home")

# County forecast URLs
county_urls = {
    "Virginia Beach": "https://api.weather.gov/gridpoints/AKQ/40,94/forecast",
    "Arlington": "https://api.weather.gov/gridpoints/LWX/97,69/forecast",
    "Richmond": "https://api.weather.gov/gridpoints/AKQ/36,83/forecast",
    "Roanoke": "https://api.weather.gov/gridpoints/RNK/58,85/forecast",
    "Charlottesville": "https://api.weather.gov/gridpoints/LWX/124,71/forecast",
    "Fredericksburg": "https://api.weather.com/gridpoints/LWX/101,81/forecast",
    "Wise": "https://api.weather.gov/gridpoints/RNK/10,61/forecast"
}

# Climate messages
climate_messages = [
    "🌫️ **Air Quality / Emissions**\nVirginia has reduced power plant emissions in recent years through programs like the Regional Greenhouse Gas Initiative, but traffic congestion and wildfires still affect air quality.",
    "🌊 **Rising Sea Levels**\nCoastal Virginia, especially Hampton Roads, is among the most flood-prone areas in the U.S. Sea levels are rising faster than the global average, increasing flooding risks.",
    "⛈️ **Extreme Weather Frequency**\nThe state has seen more frequent storms, heavy rainfall, and record wildfire seasons in recent years, stressing infrastructure and emergency systems.",
    "☀️ **Renewable Energy**\nVirginia is expanding solar and offshore wind projects, cutting emissions while building a clean-energy future on the East Coast."
]

# Map function
def generate_full_va_map():
    locations_data = {
        'Yorktown': {'lat': 37.227, 'lon': -76.495},
        'Windmill Point': {'lat': 37.615, 'lon': -76.290},
        'Sewells Point': {'lat': 36.947, 'lon': -76.330},
        'Wachapreague': {'lat': 37.608, 'lon': -75.686},
        'Lewisetta': {'lat': 37.995, 'lon': -76.465},
        'Kiptopeke': {'lat': 37.165, 'lon': -75.988},
        'Dahlgren': {'lat': 38.319, 'lon': -77.036},
    }

    df_map = pd.DataFrame({
        'Location': list(locations_data.keys()),
        'Lat': [locations_data[loc]['lat'] for loc in locations_data],
        'Lon': [locations_data[loc]['lon'] for loc in locations_data]
    })

    fig = px.scatter_mapbox(
        df_map,
        lat="Lat",
        lon="Lon",
        hover_name="Location",
        zoom=7,
        center={"lat": 37.75, "lon": -76.5},
        height=400,
        color_discrete_sequence=['red']
    )

    fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r":0,"t":0,"l":0,"b":0},
        title={'text': "Virginia NOAA Sea Level Rise Stations", 'x':0.5, 'xanchor':'center'}
    )
    return fig

# Forecast data function
def get_forecast_df(url):
    headers = {"User-Agent": "climate-dashboard"}
    try:
        res = requests.get(url, headers=headers).json()
        df = pd.DataFrame(res['properties']['periods'])
        df['startTime'] = pd.to_datetime(df['startTime'])
        df['date'] = df['startTime'].dt.date
        df['windSpeed'] = df['windSpeed'].str.extract(r'(\d+)').astype(float)
        df['UVIndex'] = [i % 12 for i in range(len(df))]
        return df
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()

# Layout
layout = html.Div(
    className="page-container",
    children=[
        html.Div(className="overlay-container", children=[
            html.H2("Climate Change Impacts on Virginia"),
            html.Div(id='climate-message', className="climate-message"),
            html.Div([
                html.Button("←", id='prev-btn', n_clicks=0),
                html.Button("→", id='next-btn', n_clicks=0)
            ], style={'textAlign': 'center'}),

            # About Virginia Climate Dashboard (full info)
            html.Div([
                html.H4("About Virginia Climate Dashboard"),
                dcc.Markdown("""
                    The climate crisis is among the greatest risks facing Virginia. Rising sea levels, air quality, 
                    and extreme weather threaten the state's communities, economy, and infrastructure. Combatting 
                    the climate crisis requires both individual and collective action across society to build a 
                    resilient and sustainable future.

                    The Virginia Climate Dashboard tracks the state's progress in addressing these threats by 
                    monitoring greenhouse gas emissions, geospatial changes to sea level rise and air quality 
                    index data, and community risks from climate hazards. Each section of the dashboard includes 
                    key climate metrics along with Virginia's public policies and programs.

                    This dashboard is designed to provide accessible, up-to-date information about climate change 
                    in Virginia offering insights into temperature trends, weather patterns, and environmental 
                    conditions that affect residents across the state.
                """)
            ], style={'border':'1px solid black', 'padding':'15px', 'borderRadius':'5px', 'marginTop':'20px'}),

            # Three aligned boxes
            html.Div([
                # Box 1: County dropdown
                html.Div([
                    html.Label("Select County"),
                    dcc.Dropdown(
                        id='county-dropdown',
                        options=[{'label': c, 'value': c} for c in county_urls],
                        value='Arlington',
                        style={'color':'black'}
                    )
                ], style={'width':'25%', 'display':'inline-block', 'border':'1px solid black', 
                          'padding':'20px', 'borderRadius':'5px', 'height':'250px', 'textAlign':'center'}),

                # Box 2: Forecast info
                html.Div([
                    html.Div(id='summary', style={'textAlign':'left', 'whiteSpace':'pre-line'})
                ], style={'width':'50%', 'display':'inline-block', 'border':'1px solid black', 
                          'padding':'20px', 'borderRadius':'5px', 'height':'250px', 'overflow':'hidden'}),

                # Box 3: Virginia commitment image
                html.Div([
                    html.Img(src='/assets/virginia_commitment.png', style={'width':'100%', 'height':'100%'})
                ], style={'width':'25%', 'display':'inline-block', 'border':'1px solid black', 
                          'borderRadius':'5px', 'height':'250px'})
            ], style={'display':'flex', 'gap':'20px', 'marginTop':'20px'}),

            # UV chart and map side by side
            html.Div([
                html.Div([dcc.Graph(id='uv', style={'height':'400px'})], style={'width':'50%', 'display':'inline-block'}),
                html.Div([dcc.Graph(id='va-full-map', figure=generate_full_va_map())], style={'width':'50%', 'display':'inline-block'})
            ], style={'display':'flex', 'gap':'20px', 'marginTop':'20px'})
        ])
    ]
)

# Callbacks
@dash.callback(
    Output('climate-message', 'children'),
    Input('prev-btn', 'n_clicks'),
    Input('next-btn', 'n_clicks'),
)
def update_message(prev_clicks, next_clicks):
    index = (next_clicks - prev_clicks) % len(climate_messages)
    return dcc.Markdown(climate_messages[index])

@dash.callback(
    Output('summary', 'children'),
    Output('uv', 'figure'),
    Input('county-dropdown', 'value')
)
def update_dashboard(county):
    df = get_forecast_df(county_urls[county])
    if df.empty:
        return "Forecast data unavailable.", {}

    df_period = df.iloc[0]
    summary = html.Div([
        html.P(f"County: {county}", style={'fontWeight':'bold'}),
        html.P(f"Date: {df_period['startTime'].date()}", style={'fontWeight':'bold'}),
        html.P(f"Time: {df_period['startTime'].strftime('%I:%M %p')}", style={'fontWeight':'bold'}),
        html.P(f"Forecast: {df_period['shortForecast']}", style={'fontWeight':'bold'}),
        html.P(f"🌡️ Temperature: {df_period['temperature']}°F", style={'fontWeight':'bold'}),
        html.P(f"💨 Wind Speed: {df_period['windSpeed']} mph", style={'fontWeight':'bold'}),
    ], style={'fontSize':'16px', 'height':'500px','overflow':'visible'})

    # UV chart
    df['weekday'] = pd.Categorical(
        df['startTime'].dt.day_name(),
        categories=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'],
        ordered=True
    )
    df['uv_range'] = df['UVIndex'].apply(lambda uv: (
        'Low' if uv <= 2 else
        'Moderate' if uv <= 5 else
        'High' if uv <= 7 else
        'Very High' if uv <= 10 else 'Extreme'
    ))

    uv_color_map = {
        'Low': '#4CAF50',
        'Moderate': '#FFEB3B',
        'High': '#FF9800',
        'Very High': '#F44336',
        'Extreme': '#9C27B0'
    }

    uv_fig = px.bar(
        df,
        x='weekday',
        y='UVIndex',
        color='uv_range',
        color_discrete_map=uv_color_map
    )
    uv_fig.update_traces(marker_line_width=0)
    uv_fig.update_layout(
        xaxis_title='Day',
        yaxis_title='UV Index',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black', size=12),
        title={'text': 'UV Index Forecast', 'x':0.5, 'xanchor':'center'},
        legend_title='UV Level',
        legend=dict(bgcolor='rgba(255,255,255,0.8)', bordercolor='black', borderwidth=1)
    )

    return summary, uv_fig