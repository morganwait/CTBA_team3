import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, callback, register_page
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta

register_page(__name__, path='/page1', name = 'Air Quality')
# --- Data ---
CITY_DATA = {
    "Williamsburg": {"lat": 37.2707, "lon": -76.7075},
    "Richmond": {"lat": 37.5407, "lon": -77.4360},
    "Virginia Beach": {"lat": 36.8529, "lon": -75.9780},
    "Roanoke": {"lat": 37.27097, "lon": -79.94143},
    "Charlottesville": {"lat": 38.0293, "lon": -78.4767},
    "Blacksburg": {"lat": 37.2296, "lon": -80.4139},
    "Norfolk": {"lat": 36.8508, "lon": -76.2859},
    "Fredericksburg": {"lat": 38.3032, "lon": -77.4605}
}

POLLUTANTS = {
    "PM2.5": "pm2_5",
    "PM10": "pm10",
    "Ozone (O₃)": "o3",
    "Nitrogen Dioxide (NO₂)": "no2",
    "Sulfur Dioxide (SO₂)": "so2",
    "Carbon Monoxide (CO)": "co"
}

IQAIR_API_KEY = "116d00e4-0ccc-445a-bd40-2f8bff94cf28"

# --- Helper functions ---
def fetch_current_aqi_iqair(city):
    url = f"http://api.airvisual.com/v2/city?city={city}&state=Virginia&country=USA&key={IQAIR_API_KEY}"
    try:
        r = requests.get(url).json()
        if "data" in r and "current" in r["data"]:
            return r["data"]["current"]["pollution"]["aqius"]
        return None
    except Exception as e:
        print(f"Error fetching AQI: {e}")
        return None

def fetch_pollutant_timeseries(lat, lon, pollutant_key):
    now = int(datetime.utcnow().timestamp())
    start = int((datetime.utcnow() - timedelta(days=2)).timestamp())

    hist_url = f"http://api.openweathermap.org/data/2.5/air_pollution/history?lat={lat}&lon={lon}&start={start}&end={now}&appid=9a9d578b2068d0df4e3e682bb181f819"
    forecast_url = f"http://api.openweathermap.org/data/2.5/air_pollution/forecast?lat={lat}&lon={lon}&appid=9a9d578b2068d0df4e3e682bb181f819"

    hist_data = requests.get(hist_url).json().get("list", [])
    forecast_data = requests.get(forecast_url).json().get("list", [])

    records = []
    for d in hist_data + forecast_data:
        dt = datetime.utcfromtimestamp(d["dt"])
        value = d["components"].get(pollutant_key)
        if value is not None:
            records.append({"datetime": dt, "value": value})
    return pd.DataFrame(records)

def aqi_level_badge(aqi):
    if aqi <= 50:
        label, color = "Good", "success"
    elif aqi <= 100:
        label, color = "Moderate", "warning"
    elif aqi <= 150:
        label, color = "Unhealthy for Sensitive Groups", "danger"
    elif aqi <= 200:
        label, color = "Unhealthy", "danger"
    else:
        label, color = "Very Unhealthy", "dark"
    return dbc.Badge(f"{label} (AQI {aqi})", color=color, className="ms-2", pill=True)

# --- Layout for Dash Page ---
layout = html.Div(children=[
    html.H2(" Virginia Air Quality Index", className="text-center mb-4"),

    dbc.Card([
        dbc.CardBody([
            html.H5("AQI for Virginia Cities", className="card-title"),
            dcc.Dropdown(
                id="aqi-city-select",
                options=[{"label": city, "value": city} for city in CITY_DATA],
                value="Williamsburg",
                clearable=False,
                style={"marginBottom": "10px"}
            ),
            html.Div(id="aqi-display")
        ])
    ], className="mb-4 shadow-sm"),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Label("Select City"),
                    dcc.Dropdown(
                        id="city-select",
                        options=[{"label": city, "value": city} for city in CITY_DATA],
                        value="Williamsburg",
                        clearable=False,
                        style={"marginBottom": "15px"}
                    ),
                    html.Label("Select Pollutant"),
                    dcc.Dropdown(
                        id="pollutant-select",
                        options=[{"label": k, "value": v} for k, v in POLLUTANTS.items()],
                        value="pm2_5",
                        clearable=False,
                        style={"marginBottom": "15px"}
                    ),
                    dbc.Button(" Refresh", id="refresh-btn", color="success", className="mt-2")
                ])
            ], className="shadow-sm")
        ], md=4),
html.Div([
                        html.H6("About the Pollutants", style={"color": "black", "marginTop": "20px"}),
                        html.Ul([
                            html.Li("PM2.5: Fine particles that penetrate deep into lungs and bloodstream. Commonly from vehicle exhaust, wildfires, and industrial emissions."),
                            html.Li("PM10: Larger particles like dust and pollen that can irritate the respiratory system."),
                            html.Li("Ozone (O₃): A reactive gas formed from sunlight and pollutants. Harmful at ground level, especially in summer."),
                            html.Li("Nitrogen Dioxide (NO₂): Emitted from vehicles and power plants. Contributes to smog and respiratory issues."),
                            html.Li("Sulfur Dioxide (SO₂): Produced by burning fossil fuels. Can trigger asthma and contribute to acid rain."),
                            html.Li("Carbon Monoxide (CO): A colorless, odorless gas from combustion. Reduces oxygen delivery in the body.")
                        ], style={"fontSize": "14px", "paddingLeft": "20px"})
                    ]),
 
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(id="pollutant-line-chart", style={"height": "600px"})
                ])
            ], className="shadow-sm")
        ], md=8)
    ])
])

# --- Callbacks ---
@callback(
    Output("pollutant-line-chart", "figure"),
    [Input("refresh-btn", "n_clicks"),
     Input("city-select", "value"),
     Input("pollutant-select", "value")]
)
def update_chart(n_clicks, selected_city, pollutant_key):
    lat, lon = CITY_DATA[selected_city]["lat"], CITY_DATA[selected_city]["lon"]
    df_line = fetch_pollutant_timeseries(lat, lon, pollutant_key)

    if df_line.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No pollutant data available for this location.",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(
            title=f"{selected_city}: {pollutant_key.upper()} Levels",
            height=600,
            margin=dict(l=20, r=20, t=40, b=20),
            #plot_bgcolor="#f0f4f8",
            #paper_bgcolor="#f0f4f8"
        )
        return fig

    fig = px.line(
        df_line,
        x="datetime",
        y="value",
        title=f"{selected_city}: {pollutant_key.upper()} Levels (Past 2 Days + Forecast)",
        labels={"value": f"{pollutant_key.upper()} (μg/m³)", "datetime": "Time"},
        markers=True
    )
    fig.update_layout(
        height=600,
        margin=dict(l=20, r=20, t=40, b=20),
        #plot_bgcolor="#f0f4f8",
        #paper_bgcolor="#f0f4f8",
        #font=dict(color="black")
    )
    return fig

@callback(
    Output("aqi-display", "children"),
    Input("aqi-city-select", "value")
)
def display_selected_city_aqi(city):
    aqi = fetch_current_aqi_iqair(city)
    if aqi is not None:
        return html.Div([
            html.Span(f"Current AQI for {city}: "),
            aqi_level_badge(aqi)
        ])
    else:
        return html.Div("AQI data for this city is currently unavailable.")
