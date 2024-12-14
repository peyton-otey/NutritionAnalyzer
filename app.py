import dash
from dash import dcc, html, Input, Output, State, ALL
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

# - - - - - DATA LOADING AND CLEANING - - - - -

def load_and_clean_data(filename):
    df = pd.read_csv(filename, low_memory=False)

    # Columns to drop due to blank entries or being unnecessary
    columns_to_drop = [
        'matched_2021', 'new_item_2022', 'serving_size_text',
        'serving_size_household', 'potassium', 'notes', 'calories_text',
        'total_fat_text', 'saturated_fat_text', 'trans_fat_text',
        'cholesterol_text', 'sodium_text', 'carbohydrates_text',
        'dietary_fiber_text', 'sugar_text', 'protein_text'
    ]

    # Remove rows with NaN in the "serving_size" column and drop unnecessary columns
    df = df.dropna(subset=['serving_size']).drop(columns=columns_to_drop)

    # Replace NaN in 'serving_size_unit' with 'Unit'
    df['serving_size_unit'] = df['serving_size_unit'].fillna('Unit')

    # Remove duplicate rows
    df = df.drop_duplicates()

    # Nutrition columns to be converted to numeric
    nutrition_columns = [
        'calories_(kCal)', 'total_fat_(g)', 'saturated_fat_(g)', 'trans_fat_(g)', 'cholesterol_(mg/dL)',
        'sodium_(mg)', 'carbohydrates_(g)', 'dietary_fiber_(g)', 'sugar_(g)', 'protein_(g)'
    ]

    # Convert nutrition columns to numeric, replacing non-numeric entries with NaN
    df[nutrition_columns] = df[nutrition_columns].apply(pd.to_numeric, errors='coerce')

    # Calculate macronutrient calories
    df['carb_calories'] = df['carbohydrates_(g)'] * 4
    df['fat_calories'] = df['total_fat_(g)'] * 9
    df['protein_calories'] = df['protein_(g)'] * 4

    return df, nutrition_columns

# Load the data
df, nutrition_columns = load_and_clean_data("ms_annual_data_2022.csv")

# - - - - - DASH APP SETUP - - - - -

# Set suppress_callback_exceptions to True
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.JOURNAL], suppress_callback_exceptions=True)
server = app.server  # Needed for deployment

# - - - - - LAYOUT COMPONENTS - - - - -

# Header with navigation links centered
header = html.Div([
    html.H1("Restaurant Nutrition Dashboard", style={'textAlign': 'center'}),
    html.Hr(),
    dbc.Nav(
        [
            dbc.NavLink("Explore Foods", href="/explore", id={"type": "navlink", "index": 0}, active="exact", className="nav-link mx-5"),
            dbc.NavLink("Compare Foods", href="/compare", id={"type": "navlink", "index": 1}, active="exact", className="nav-link mx-5"),
            dbc.NavLink("Analytics", href="/analytics", id={"type": "navlink", "index": 2}, active="exact", className="nav-link mx-5"),
        ],
        pills=True,
        justified=True,
    ),
    html.Hr(),
])

# Main content layout
content = html.Div(
    id="page-content",
    style={
        "padding": "2rem 1rem",
        "overflow": "auto",
        "height": "calc(100vh - 210px)",
    },
)

# App layout
app.layout = html.Div(
    html.Div([
        dcc.Location(id="url"),
        header,
        content
    ], style={"padding": "2rem 1rem", "overflow": "auto", "paddingLeft": "5%", "paddingRight": "5%"})
)

# - - - - - PAGE LAYOUTS - - - - -

def explore_layout():
    return html.Div([
        html.H2("Explore Nutrition Information"),
        html.Hr(),
        dbc.Row([
            dbc.Col([
                dbc.Row([
                    dbc.Label("Select Restaurant"),
                    dcc.Dropdown(
                        id='restaurant-dropdown',
                        options=[{'label': r, 'value': r} for r in sorted(df['restaurant'].unique())],
                        placeholder='Select a restaurant',
                        clearable=True,
                    ),
                ],),
                html.Br(),
                dbc.Row([
                    dbc.Label("Select Food Category"),
                    dcc.Dropdown(
                        id='category-dropdown',
                        placeholder='Select a food category',
                        clearable=True,
                    ),
                ]),
                html.Br(),
                dbc.Row([
                    dbc.Label("Select Food Item"),
                    dcc.Dropdown(
                        id='item-dropdown',
                        placeholder='Select a food item',
                        clearable=True,
                    ),
                ]),
            ], md=4),
            dbc.Col([
                html.Iframe(
                    id='google-map',
                    src="",
                    style={"width": "100%", "height": "400px", "border": "0"},
                    allow="fullscreen",  # Enable fullscreen by setting "allow" attribute
                    title="Google Map"
                ),
            ], width=8),
        ], className="mb-4"),
        html.Div(id='item-info-output'),
    ])

def compare_layout():
    return html.Div([
        html.H2("Compare Food Items"),
        html.Hr(),
        dbc.Row([
            dbc.Col([
                dbc.Label("Select Food Items"),
                dcc.Dropdown(
                    id='compare-items-dropdown',
                    options=[{'label': item, 'value': item} for item in sorted(df['item_name'].unique())],
                    placeholder='Select food items to compare',
                    multi=True,
                    clearable=True,
                ),
            ], md=12),
        ], className="mb-4"),
        dbc.Row([
            dbc.Col([
                dbc.Label("Select Nutrition Metrics"),
                dcc.Dropdown(
                    id='compare-metrics-dropdown',
                    options=[{'label': n.replace('_', ' ').title(), 'value': n} for n in nutrition_columns],
                    placeholder='Select nutrition metrics to compare',
                    multi=True,
                    clearable=True,
                ),
            ], md=12),
        ], className="mb-4"),
        html.Div(id='compare-output'),
    ])

def analytics_layout():
    return dbc.Container([
        html.H2("Data Analytics"),
        html.Hr(),
        dbc.Tabs([
            dbc.Tab(label='Distribution', tab_id='distribution'),
            dbc.Tab(label='Top Foods', tab_id='top-n'),
            dbc.Tab(label='Restaurant Comparison', tab_id='restaurant-averages'),
            dbc.Tab(label='Compare Categories', tab_id='category-comparison'),
            dbc.Tab(label='Statistical Summary', tab_id='statistical-summary'),
        ], id='analytics-tabs', active_tab='distribution'),
        html.Div(id='analytics-content')
    ], fluid=True)

# - - - - - CALLBACKS - - - - -

# Update page content based on URL
@app.callback(
    [Output("page-content", "children"),
     Output({"type": "navlink", "index": ALL}, "active")],
    [Input("url", "pathname")],
)
def render_page_content(pathname):
    if pathname == "/" or pathname == "/explore":
        return explore_layout(), [True, False, False]
    elif pathname == "/compare":
        return compare_layout(), [False, True, False]
    elif pathname == "/analytics":
        return analytics_layout(), [False, False, True]
    else:
        return html.Div([
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognized...")
        ]), [False, False, False]
@app.callback(
    Output('google-map', 'src'),
    [Input('restaurant-dropdown', 'value')]
)
def update_map(selected_restaurant):
    if selected_restaurant is None:
        return ""
    
    # URL for Google Maps search near Carbondale, IL for the selected restaurant
    google_map_url = f"https://www.google.com/maps/embed/v1/search?key=INSERTKEY={selected_restaurant}"
    return google_map_url
    
# Update category dropdown based on selected restaurant
@app.callback(
    Output('category-dropdown', 'options'),
    [Input('restaurant-dropdown', 'value'),
     Input('item-dropdown', 'value')]
)
def update_category_dropdown(selected_restaurant, selected_item):
    if selected_item and not selected_restaurant:
        # Autofill restaurant and category based on selected item
        item_row = df[df['item_name'] == selected_item].iloc[0]
        return [{'label': item_row['food_category'], 'value': item_row['food_category']}]
    elif selected_restaurant:
        filtered_df = df[df['restaurant'] == selected_restaurant]
        categories = filtered_df['food_category'].unique()
        return [{'label': c, 'value': c} for c in sorted(categories)]
    else:
        # If no restaurant is selected, show all categories
        categories = df['food_category'].unique()
        return [{'label': c, 'value': c} for c in sorted(categories)]

# Update item dropdown based on selected restaurant and category
@app.callback(
    Output('item-dropdown', 'options'),
    [Input('restaurant-dropdown', 'value'),
     Input('category-dropdown', 'value')]
)
def update_item_dropdown(selected_restaurant, selected_category):
    if selected_restaurant and selected_category:
        filtered_df = df[(df['restaurant'] == selected_restaurant) & (df['food_category'] == selected_category)]
    elif selected_restaurant:
        filtered_df = df[df['restaurant'] == selected_restaurant]
    elif selected_category:
        filtered_df = df[df['food_category'] == selected_category]
    else:
        # If neither restaurant nor category is selected, show all items
        filtered_df = df
    items = filtered_df['item_name'].unique()
    return [{'label': i, 'value': i} for i in sorted(items)]

# Autofill restaurant and category when item is selected
@app.callback(
    [Output('restaurant-dropdown', 'value'),
     Output('category-dropdown', 'value')],
    [Input('item-dropdown', 'value')],
    [State('restaurant-dropdown', 'value'),
     State('category-dropdown', 'value')]
)
def autofill_restaurant_category(selected_item, current_restaurant, current_category):
    if selected_item:
        item_row = df[df['item_name'] == selected_item]
        
        # If the current restaurant is None or does not match the selected item, update it
        if current_restaurant is None or current_restaurant not in item_row['restaurant'].values:
            restaurant = item_row.iloc[0]['restaurant']
        else:
            restaurant = current_restaurant  # Retain the current selection if it matches
        
        category = item_row.iloc[0]['food_category']
        return restaurant, category
    else:
        return current_restaurant, current_category

# Display item information for selected item
@app.callback(
    Output('item-info-output', 'children'),
    [Input('item-dropdown', 'value')]
)
def display_item_info(selected_item):
    if selected_item:
        # Retrieve the selected item data
        item_data = df[df['item_name'] == selected_item].iloc[0]
        # Create output components
        outputs = []
        outputs.append(html.H4(selected_item))
        outputs.append(html.P(f"Restaurant: {item_data['restaurant']}"))
        outputs.append(html.P(f"Food Category: {item_data['food_category']}"))
        description = item_data['item_description'] if pd.notnull(item_data['item_description']) else "No description available."
        outputs.append(html.P(f"Description: {description}"))
        serving_size = f"{item_data['serving_size']} {item_data['serving_size_unit']}"
        outputs.append(html.P(f"Serving Size: {serving_size}"))
        # Caloric breakdown pie chart
        labels = ['Carbohydrates', 'Fats', 'Proteins']
        values = [item_data['carb_calories'], item_data['fat_calories'], item_data['protein_calories']]
        fig = px.pie(
            names=labels,
            values=values,
            title='Caloric Breakdown by Macronutrient',
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        outputs.append(dcc.Graph(figure=fig))
        # Nutrition Information
        nutrition_info = item_data[nutrition_columns].to_dict()
        table_rows = [
            html.Tr([html.Td(n.replace('_', ' ').title()), html.Td(f"{v}")])
            for n, v in nutrition_info.items() if pd.notnull(v)
        ]
        table = dbc.Table([
            html.Thead(
                html.Tr([html.Th("Nutrient"), html.Th("Amount")])
            ),
            html.Tbody(table_rows)
        ], bordered=True, hover=True, striped=True)
        outputs.append(html.H5("Nutrition Information"))
        outputs.append(table)
        return html.Div(outputs)
    # else:
    #     # Display a placeholder graph to prevent clipping
    #     fig = go.Figure()
    #     fig.update_layout(
    #         title='Item Information',
    #         xaxis={'visible': False},
    #         yaxis={'visible': False},
    #         height=400  # Adjust height as needed
    #     )
    #     return dcc.Graph(figure=fig)
    

# Update compare output based on selected items and metrics
@app.callback(
    Output('compare-output', 'children'),
    [Input('compare-items-dropdown', 'value'),
     Input('compare-metrics-dropdown', 'value')]
)
def update_compare_output(selected_items, selected_metrics):
    if selected_items and selected_metrics:
        compare_df = df[df['item_name'].isin(selected_items)]
        melted_df = compare_df.melt(
            id_vars=['item_name'],
            value_vars=selected_metrics,
            var_name='Nutrient',
            value_name='Amount'
        )
        fig = px.bar(
            melted_df,
            x='Nutrient',
            y='Amount',
            color='item_name',
            barmode='group',
            title='Nutrition Comparison',
            labels={
                'Nutrient': 'Nutrient',
                'Amount': 'Amount',
                'item_name': 'Item Name'
            },
            template='simple_white'
        )
        return dcc.Graph(figure=fig)
    # else:
    #     # Display a blank graph when inputs are not selected
    #     fig = px.bar(title='Nutrition Comparison')
    #     fig.update_layout(xaxis={'visible': False}, yaxis={'visible': False})
    #     return dcc.Graph(figure=fig)

# Update analytics content based on selected tab
@app.callback(
    Output('analytics-content', 'children'),
    [Input('analytics-tabs', 'active_tab')]
)
def render_analytics_tab(active_tab):
    if active_tab == 'distribution':
        return nutritional_distribution_layout()
    elif active_tab == 'top-n':
        return top_n_foods_layout()
    elif active_tab == 'restaurant-averages':
        return restaurant_averages_layout()
    elif active_tab == 'category-comparison':
        return category_comparison_layout()
    elif active_tab == 'statistical-summary':
        return statistical_summary_layout()
    else:
        return html.Div()

# Layouts for each analytics tab
def nutritional_distribution_layout():
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Label("Select Nutrient"),
                dcc.Dropdown(
                    id='dist-nutrient-dropdown',
                    options=[{'label': n.replace('_', ' ').title(), 'value': n} for n in nutrition_columns],
                    placeholder='Select a nutrient',
                    clearable=True,
                ),
            ], md=6),
            dbc.Col([
                dbc.Label("Group By"),
                dcc.Dropdown(
                    id='dist-groupby-dropdown',
                    options=[
                        {'label': 'Restaurant', 'value': 'restaurant'},
                        {'label': 'Food Category', 'value': 'food_category'}
                    ],
                    placeholder='Select a grouping variable',
                    clearable=True,
                ),
            ], md=6),
        ], className="mb-4"),
        html.P("You can zoom in on the graph by clicking and dragging on the graph, and zoom out by double-clicking on the graph."),
        html.Div(id='distribution-output'),
    ])

def top_n_foods_layout():
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Label("Select Nutrient"),
                dcc.Dropdown(
                    id='top-nutrient-dropdown',
                    options=[{'label': n.replace('_', ' ').title(), 'value': n} for n in nutrition_columns],
                    placeholder='Select a nutrient',
                    clearable=True,
                ),
            ], md=4),
            dbc.Col([
                dbc.Label("Number of Top Items"),
                dcc.Input(
                    id='top-n-input',
                    type='number',
                    value=10,
                    min=1,
                    max=50,
                    step=1,
                ),
            ], md=4),
            dbc.Col([
                dbc.Label("Sort Order"),
                dcc.RadioItems(
                    id='top-n-order',
                    options=[
                        {'label': 'Highest', 'value': 'desc'},
                        {'label': 'Lowest', 'value': 'asc'}
                    ],
                    value='desc',
                    inline=True
                ),
            ], md=4),
        ], className="mb-4"),
        html.Div(id='top-n-output'),
    ])

def restaurant_averages_layout():
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Label("Select Restaurants"),
                dcc.Dropdown(
                    id='rest-avg-restaurants-dropdown',
                    options=[{'label': r, 'value': r} for r in sorted(df['restaurant'].unique())],
                    multi=True,
                    placeholder='Select restaurants',
                    clearable=True,
                ),
            ], md=12),
        ], className="mb-4"),
        dbc.Row([
            dbc.Col([
                dbc.Label("Select Nutrients"),
                dcc.Dropdown(
                    id='rest-avg-nutrients-dropdown',
                    options=[{'label': n.replace('_', ' ').title(), 'value': n} for n in nutrition_columns],
                    multi=True,
                    placeholder='Select nutrients',
                    clearable=True,
                ),
            ], md=12),
        ], className="mb-4"),
        html.Div(id='restaurant-averages-output'),
    ])

def category_comparison_layout():
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Label("Select Nutrient"),
                dcc.Dropdown(
                    id='cat-comp-nutrient-dropdown',
                    options=[{'label': n.replace('_', ' ').title(), 'value': n} for n in nutrition_columns],
                    placeholder='Select a nutrient',
                    clearable=True,
                ),
            ], md=6),
            dbc.Col([
                dbc.Label("Select Categories to Compare"),
                dcc.Dropdown(
                    id='cat-comp-categories-dropdown',
                    options=[{'label': c, 'value': c} for c in sorted(df['food_category'].unique())],
                    multi=True,
                    placeholder='Select categories',
                    clearable=True,
                ),
            ], md=6),
        ], className="mb-4"),
        html.Div(id='category-comparison-output'),
    ])

def statistical_summary_layout():
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Label("Select Nutrient"),
                dcc.Dropdown(
                    id='stat-sum-nutrient-dropdown',
                    options=[{'label': n.replace('_', ' ').title(), 'value': n} for n in nutrition_columns],
                    placeholder='Select a nutrient',
                    clearable=True,
                ),
            ], md=6),
            dbc.Col([
                dbc.Label("Group By"),
                dcc.Dropdown(
                    id='stat-sum-groupby-dropdown',
                    options=[
                        {'label': 'Restaurant', 'value': 'restaurant'},
                        {'label': 'Food Category', 'value': 'food_category'}
                    ],
                    placeholder='Select a grouping variable',
                    clearable=True,
                ),
            ], md=6),
        ], className="mb-4"),
        html.Div(id='statistical-summary-output'),
    ])

# Callbacks for Nutritional Distribution
@app.callback(
    Output('distribution-output', 'children'),
    [Input('dist-nutrient-dropdown', 'value'),
     Input('dist-groupby-dropdown', 'value')]
)
def update_distribution_output(selected_nutrient, group_by):
    if selected_nutrient and group_by:
        fig = px.box(
            df,
            x=group_by,
            y=selected_nutrient,
            title=f'Distribution of {selected_nutrient.replace("_", " ").title()} by {group_by.replace("_", " ").title()}',
            labels={
                group_by: group_by.replace('_', ' ').title(),
                selected_nutrient: selected_nutrient.replace('_', ' ').title()
            },
            template='simple_white'
        )
        return dcc.Graph(figure=fig)
    # else:
    #     # Display a blank graph when inputs are not selected
    #     fig = px.box(title='Distribution')
    #     fig.update_layout(xaxis={'visible': False}, yaxis={'visible': False})
    #     return dcc.Graph(figure=fig)

# Callbacks for Top N Foods
@app.callback(
    Output('top-n-output', 'children'),
    [Input('top-nutrient-dropdown', 'value'),
     Input('top-n-input', 'value'),
     Input('top-n-order', 'value')]
)
def update_top_n_output(selected_nutrient, n, order):
    if selected_nutrient and n:
        sorted_df = df[['item_name', 'restaurant', selected_nutrient]].dropna(subset=[selected_nutrient])
        sorted_df = sorted_df.sort_values(by=selected_nutrient, ascending=(order == 'asc'))
        top_n_df = sorted_df.head(n)
        fig = px.bar(
            top_n_df,
            x='item_name',
            y=selected_nutrient,
            color='restaurant',
            title=f'Top {n} Foods by {selected_nutrient.replace("_", " ").title()}',
            labels={
                'item_name': 'Food Item',
                selected_nutrient: selected_nutrient.replace('_', ' ').title()
            },
            template='simple_white'
        )
        return dcc.Graph(figure=fig)
    # else:
    #     # Display a blank graph when inputs are not selected
    #     fig = px.bar(title='Top Foods')
    #     fig.update_layout(xaxis={'visible': False}, yaxis={'visible': False})
    #     return dcc.Graph(figure=fig)

# Callbacks for Restaurant Averages
@app.callback(
    Output('restaurant-averages-output', 'children'),
    [Input('rest-avg-restaurants-dropdown', 'value'),
     Input('rest-avg-nutrients-dropdown', 'value')]
)
def update_restaurant_averages_output(selected_restaurants, selected_nutrients):
    if selected_restaurants and selected_nutrients:
        filtered_df = df[df['restaurant'].isin(selected_restaurants)]
        avg_df = filtered_df.groupby('restaurant')[selected_nutrients].mean().reset_index()
        melted_df = avg_df.melt(
            id_vars='restaurant',
            value_vars=selected_nutrients,
            var_name='Nutrient',
            value_name='Average Amount'
        )
        fig = px.bar(
            melted_df,
            x='restaurant',
            y='Average Amount',
            color='Nutrient',
            barmode='group',
            title='Average Nutrient Amounts by Restaurant',
            labels={
                'restaurant': 'Restaurant',
                'Average Amount': 'Average Amount'
            },
            template='simple_white'
        )
        return dcc.Graph(figure=fig)
    # else:
    #     # Display a blank graph when inputs are not selected
    #     fig = px.bar(title='Restaurant Comparison')
    #     fig.update_layout(xaxis={'visible': False}, yaxis={'visible': False})
    #     return dcc.Graph(figure=fig)

# Callbacks for Category Comparison
@app.callback(
    Output('category-comparison-output', 'children'),
    [Input('cat-comp-nutrient-dropdown', 'value'),
     Input('cat-comp-categories-dropdown', 'value')]
)
def update_category_comparison_output(selected_nutrient, selected_categories):
    if selected_nutrient and selected_categories:
        filtered_df = df[df['food_category'].isin(selected_categories)]
        avg_df = filtered_df.groupby('food_category')[selected_nutrient].mean().reset_index()
        fig = px.bar(
            avg_df,
            x='food_category',
            y=selected_nutrient,
            title=f'Average {selected_nutrient.replace("_", " ").title()} by Food Category',
            labels={
                'food_category': 'Food Category',
                selected_nutrient: f'Average {selected_nutrient.replace("_", " ").title()}'
            },
            template='simple_white'
        )
        return dcc.Graph(figure=fig)
    # else:
    #     # Display a blank graph when inputs are not selected
    #     fig = px.bar(title='Category Comparison')
    #     fig.update_layout(xaxis={'visible': False}, yaxis={'visible': False})
    #     return dcc.Graph(figure=fig)

# Callbacks for Statistical Summary
@app.callback(
    Output('statistical-summary-output', 'children'),
    [Input('stat-sum-nutrient-dropdown', 'value'),
     Input('stat-sum-groupby-dropdown', 'value')]
)
def update_statistical_summary_output(selected_nutrient, group_by):
    if selected_nutrient and group_by:
        summary_df = df.groupby(group_by)[selected_nutrient].agg(['mean', 'median', 'std', 'min', 'max']).reset_index()
        summary_df = summary_df.round(2)
        table = dbc.Table.from_dataframe(
            summary_df,
            striped=True,
            bordered=True,
            hover=True,
            responsive=True
        )
        return html.Div([
            html.H4(f'Statistical Summary of {selected_nutrient.replace("_", " ").title()} by {group_by.replace("_", " ").title()}'),
            table
        ])
    else:
        # Display a message when inputs are not selected
        return html.Div([
            html.H4('Statistical Summary'),
            html.P('Please select a nutrient and a grouping variable to view the statistical summary.')
        ])

# - - - - - RUN THE APP - - - - -

if __name__ == '__main__':
    app.run_server(debug=True, host='127.0.0.1')
