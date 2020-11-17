from datetime import datetime
import json
import re
import sqlite3

import numpy as np 
import pandas as pd
import geopandas as gpd

import plotly.graph_objs as go
import plotly.express as px


# get data functions ###################################################################################################

def get_df():
    return pd.read_csv("https://github.com/oena/bios823_final_project/blob/master/dashboard/dashboard_data/cleaned_data_for_viz.tsv", sep="\t")

def get_gdf():
    """
    this function will load country geo data, which is necessary for creating map plot
    """
    # load the data of geo information
    shapefile = '50m_cultural/ne_50m_admin_0_countries.shp'
    gdf = gpd.read_file(shapefile)[['ADMIN', 'geometry']]
    gdf = gdf[gdf.ADMIN != 'Antarctica']  # drop Antarctica since no people lives there
    gdf['ADMIN'] = gdf.ADMIN.apply(lambda x: x.upper())

    return gdf
    
def get_data_for_map(df=get_df(), gdf=get_gdf()):
    country_count_df = (
        df
        # add criteria here
        [['Location_Country']]
        [(df['Location_Country'] != 'NAN') & (df['Location_Country'] != 'REPUBLIC OF')].
        # the last criteria can be drop when we confirm what 'REPUBLIC OF' is
        assign(count=1).
        groupby(['Location_Country']).
        agg('sum').
        sort_values('count', ascending=False)
    )

    # equip data with geo info
    geo_country_count_df = (
        gdf.merge(country_count_df, left_on='ADMIN', right_on='Location_Country', how='left').
        sort_values('count', ascending=False)
    )


    return country_count_df, geo_country_count_df

# location viz functions ###############################################################################################

def get_country_plot(country_count_df,
                     geo_country_count_df,
                     center="world"):
    """
    this function generate the plot to demonstrate how many trial in the each countries
    Parameters
    ----------
    center: str
        the center for the plot, options:
        'world',
        'europe',
        'north_america',
        'south_america',
        'africa',
        'asia',
        'oceania'
    Returns
    ----------
    geo_plot:
        the plot demonstrate how many trial in the each countries
    """
    # Convert to geojson
    geo_country_count_json = json.loads(geo_country_count_df.to_json())
    
    # Center of the Plot data
    regions = {
        'world': {"lat": 45, "lon": 0, 'zoom': 0.75},
        'europe': {'lat': 50, 'lon': 0, 'zoom': 3},
        'north_america': {'lat': 40, 'lon': -100, 'zoom': 2},
        'south_america': {'lat': -15, 'lon': -60, 'zoom': 2},
        'africa': {'lat': 0, 'lon': 20, 'zoom': 2},
        'asia': {'lat': 30, 'lon': 100, 'zoom': 2},
        'oceania': {'lat': -10, 'lon': 130, 'zoom': 2},
    }

    geo_plot = px.choropleth_mapbox(
        data_frame=geo_country_count_df,
        geojson=geo_country_count_json,
        color='count',
        locations='ADMIN',
        featureidkey='properties.ADMIN',
        mapbox_style='carto-positron',  # can change background
        color_continuous_scale=px.colors.sequential.YlGnBu,  # make colorscale fix
        # we can change our center
        center={"lat":regions[center]["lat"], "lon":regions[center]["lon"]},
        zoom=regions[center]["zoom"],
        opacity=0.75,
        labels={"ADMIN": "Country",
                "count": "Count of Trials",
                },
    )
    # the size of figure may need adjust
    geo_plot.update_layout(margin={"r": 0, "t": 10, "l": 0, "b": 0},
                           height=650,
                           width=950,
                           )

    return geo_plot


# trial duration functions #############################################################################################

def get_trail_duration_plot(df=get_df(), sort_by="count", type="bar"):
    """
    this function generate the plot to demonstrate how trial duration distribute
    Parameters
    ----------
    df : pandas.DataFrame
        df data frame
    sort_by : str
        sort by "count" or "Trial_Duration"
    type: str
        the type of the plot, "pie" or "bar"
    Returns
    ----------
    plot:
        the plot demonstrate how trial duration distribute
    """
    duration_df = df.Trial_Duration_Category.value_counts().to_frame().reset_index()
    duration_df.columns = ['Trial_Duration', 'count']

    # control bar for how to order the bar chart: 'count' or 'Trial_Duration'

    duration_order = ['less then 1 month',
                      '1 - 3 months',
                      '4 - 6 months',
                      '7 - 12 months',
                      '1 - 2 years',
                      '2 - 5 years',
                      '5 - 10 years',
                      'over 10 years']
                      
    # in case some cats have no value
    for x in duration_order:
        if x not in [x for x in duration_df.Trial_Duration]:
            duration_df=duration_df.append({"Trial_Duration":x,"count":0}, ignore_index=True)
        
    duration_df['Trial_Duration'] = duration_df['Trial_Duration'].astype('category')
    duration_df['Trial_Duration'].cat.reorder_categories(duration_order, inplace=True)
    duration_df.sort_values(sort_by, inplace=True)

    if type == "pie":
        plot = px.pie(duration_df,
                      values='count',
                      names='Trial_Duration',
                      color_discrete_sequence=px.colors.sequential.YlGnBu_r,
                      labels={"Trial_Duration": "Trial Duration",
                              "count": "Count of Trials"},
#                      title='Project duration COVID-19 Trial'
                      )
    elif type == "bar":
        plot = px.bar(duration_df,
                      x='Trial_Duration',
                      y='count',
                      color='count',
                      color_continuous_scale='deep',
                      labels={'count': 'Count of Trials',
                              'Trial_Duration': 'Trial Duration'},
#                      title='Project duration COVID-19 Trial'
                      )

    return plot


# enrollment functions #################################################################################################

def get_enrollment_plot(df=get_df(), sort_by="count", type="bar"):
    """
    this function generate the plot to demonstrate how enrollment distribute
    Parameters
    ----------
    df : pandas.DataFrame
        df data frame
    sort_by : str
        sort by "count" or "Enrollment"
    type: str
        the type of the plot, "pie" or "bar"
    Returns
    ----------
    plot:
        the plot demonstrate how enrollment distribute
    """
    enroll_df = df.Enrollment_Category.value_counts().to_frame().reset_index()
    enroll_df.columns = ['Enrollment', 'count']

    # control bar for how to order the bar chart: 'count' or 'enroll'

    enroll_order = ['less then 10',
                    '11 - 50',
                    '51 - 100',
                    '101 - 200',
                    '201 - 500',
                    '501 - 1000',
                    '1001 - 5000',
                    '5001 - 10000',
                    'over 10000']
                    
    # in case some cats have no value
    for x in enroll_order:
        if x not in [x for x in enroll_df.Enrollment]:
            enroll_df=enroll_df.append({"Enrollment":x,"count":0}, ignore_index=True)
            
    enroll_df['Enrollment'] = enroll_df['Enrollment'].astype('category')
    enroll_df['Enrollment'].cat.reorder_categories(enroll_order, inplace=True)
    enroll_df.sort_values(sort_by, inplace=True)

    if type == "pie":
        plot = px.pie(enroll_df,
                      values='count',
                      names='Enrollment',
                      color_discrete_sequence = px.colors.sequential.YlGnBu_r,
                      labels={"count": "Count of Trials"},
#                      title='Number of Participants in COVID-19 Trial Project'
                      )
    elif type == "bar":
        plot = px.bar(enroll_df,
                      x='Enrollment',
                      y='count',
                      color='count',
                      color_continuous_scale = 'deep',
                      labels={'count':'Count of Trials'},
#                      title='Number of Participants in COVID-19 Trial Project'
                      )
    return plot


# catgorical plot ######################################################################################################

def get_cat_plot(df=get_df(), var="Status", type="bar"):
    """
    this function generate the plot of categorical variable
    Parameters
    ----------
    df : pandas.DataFrame
        df data frame
    var : str
        choose the categorical variable to plot, "Statue", "Age" or "Phases"
    type: str
        the type of the plot, "pie" or "bar"
    start: datetime
        the lower bound of time range for the plot
    end: datetime
        the upper bound of time range for the plot
    Returns
    ----------
    plot:
        the plot of categorical variable
    """
    vars = {"Status": ('Status', 'Status of COVID-19 Trial Project'),
             "Age": ('Age', 'Participants Age of COVID-19 Trial Project'),
             "Phases": ('Phases', 'Phases of COVID-19 Trial Project'),
             "Funded Bys": ("Funded Bys", "COVID-19 Trial Project are Funded By")}

    var = vars[var]

    def plot_pie(df, col, title_str):
        # only slice top 11 categories
        df = df[col].dropna().value_counts().to_frame().reset_index().head(11)
        df.columns = [col, 'count']
        plot = px.pie(df,
                      values='count',
                      names=col,
                      color_discrete_sequence=px.colors.sequential.deep_r,
                      labels={"count": "Count of Trials"},
#                      title=title_str
                      )
        return plot

    def plot_bar(df, col, title_str):
        df = df[col].dropna().value_counts().to_frame().reset_index().head(11)
        df.columns = [col, 'count']
        df = df.sort_values('count', ascending=True)
        plot = px.bar(df,
                      x=col,
                      y='count',
                      color='count',
                      color_continuous_scale='deep',
                      labels={"count": "Count of Trials"},
#                      title=title_str
                      )
        return plot

    if type == "bar":
        plot = plot_bar(df, *var)
    elif type == "pie":
        plot = plot_pie(df, *var)

    return plot


# test #################################################################################################################

if __name__=="__main__":
#    get_country_plot(*get_data_for_map(),center='europe').show()
    gdf = gpd.read_file("/Users/yuehan/Desktop/Duke/20Fall/BIOSTA823/final_project/dash/cleaned_data_for_map_with_geo.tsv"
             ,GEOM_POSSIBLE_NAMES="geometry",KEEP_GEOM_COLUMNS="NO")
    gdf["count"] = gdf["count"].replace({"":0})
    gdf = gdf.astype({"count":"float"})
    get_country_plot(pd.read_csv("cleaned_data_for_map.tsv", sep="\t"),
                     gdf,
                     center='europe').show()
    get_trail_duration_plot(sort_by="count",type = "bar").show()
    get_enrollment_plot(sort_by='Enrollment').show()
    get_cat_plot(var="Age",type="pie").show()




