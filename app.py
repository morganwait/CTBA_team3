import dash
from dash import html
import dash_bootstrap_components as dbc

# Initialize the app with Dash Pages enabled
app = dash.Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    title="Virginia Climate Dashboard",
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

server = app.server

# Layout with navigation bar and page container
app.layout = html.Div([
    dbc.NavbarSimple(
        children=[
            dbc.NavLink('Home', href='/', active='exact'),
            dbc.NavLink('Air Quality', href='/page1', active='exact'),
            dbc.NavLink('Rising Sea Levels', href='/page2', active='exact'),
            dbc.NavLink('Extreme Weather Frequency', href='/page3', active='exact'),
            
        ],
        brand="Virginia Climate Dashboard",
        color= "#0d4464",
        dark=True,
        className="mb-4"
    ),
    dash.page_container
])

if __name__ == "__main__":
    app.run(debug=True)
