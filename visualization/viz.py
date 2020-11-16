from datetime import datetime
import json
import re

import numpy as np 
import pandas as pd
import geopandas as gpd

import plotly.graph_objs as go
import plotly.express as px


# get data functions ###################################################################################################

def get_df():
    """
    this function load cleaned data and then transform it to df, which will be use to generate visualization
    """
    # Read in dataset
    path = 'cleaned_covid_studies_092020.tsv'
    covid_trials_df = pd.read_csv(path, sep="\t", index_col=0)

    # drop duplicates
    covid_trials_df = covid_trials_df.drop_duplicates()

    # Preprocessing data

    ## drop exploded
    exploded_cols = ["Interventions",
                     "Outcome Measures",
                     "Sponsor/Collaborators",
                     "Funded Bys",
                     "Study Type",
                     "Study Designs",
                     "Conditions"]
    df = covid_trials_df.drop(columns=exploded_cols).drop_duplicates()

    ## age
    df['Age'] = df.Age.str.extract(r'[(](.*?)[)]')

    ## date
    date_columns = ['Start Date',
                    'Completion Date',
                    'First Posted',
                    'Last Update Posted']

    def rep_m(m):
        months = ["January", "February", "March", "April", "May", "June", "July",
                  "August", "September", "October", "November", "December"]
        months = [x.upper() for x in months]
        for i in months:
            if m == i:
                m = months.index(i) + 1
        return str(m)

    def to_date(date_str):
        if date_str == "NAN NAN":
            return np.nan
        else:
            date_str = date_str.split()
            Y = date_str[1]
            m = rep_m(date_str[0])

            date = datetime.strptime(Y + "-" + m, "%Y-%m")

            return date

    df[date_columns] = df[date_columns].applymap(to_date)

    ## trial duration
    def get_interval_day(arrLike, start, end):
        start_date = arrLike[start]
        end_date = arrLike[end]

        return (end_date - start_date).days

    # https://blog.csdn.net/u010339879/article/details/79505570
    def month_delta(start_date, end_date):
        flag = True
        if start_date > end_date:
            start_date, end_date = end_date, start_date
            flag = False
        year_diff = end_date.year - start_date.year
        end_month = year_diff * 12 + end_date.month
        delta = end_month - start_date.month
        return -delta if flag is False else delta

    def get_interval_month(arrLike, start, end):
        start_date = arrLike[start]
        end_date = arrLike[end]

        return month_delta(start_date, end_date)

    df['Trial_Duration_Days'] = df.apply(
        get_interval_day, axis=1, args=('Start Date', 'Completion Date'))

    df['Trial_Duration_Months'] = df.apply(
        get_interval_month, axis=1, args=('Start Date', 'Completion Date'))

    return df

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

def get_gdf_state():
    """
    this function will load US state geo data, which is necessary for creating map plot
    """
    # load the data of geo information
    shapefile_state = '50m_cultural/ne_50m_admin_1_states_provinces.shp'
    gdf_state = gpd.read_file(shapefile_state)
    gdf_state = (
        gdf_state[gdf_state.adm1_code.str.startswith("USA")]
        [['name', 'geometry']]
    )
    gdf_state.name = gdf_state.name.apply(lambda x: x.upper())

    return gdf_state


# location viz functions ###############################################################################################

def get_country_plot(df=get_df(), gdf=get_gdf(), start=datetime(1900,1,1), end=datetime(2099,12,31), center="world"):
    """
    this function generate the plot to demonstrate how many trial in the each countries
    Parameters
    ----------
    df : pandas.DataFrame
        df data frame
    gdf : pandas.DataFrame
        gdf data frame
    start: datetime
        the lower bound of time range for the plot
    end: datetime
        the upper bound of time range for the plot
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
    # match country name
    def rename_country(old_name):
        name_match = {
            'UNITED STATES': 'UNITED STATES OF AMERICA',
            'RUSSIAN FEDERATION': 'RUSSIA',
            'HONG KONG': 'HONG KONG S.A.R.',
            'CONGO': 'DEMOCRATIC REPUBLIC OF THE CONGO',
            'NORTH MACEDONIA': 'MACEDONIA',
            'CÔTE D\'IVOIRE': 'IVORY COAST',
            'FRENCH GUIANA': 'GUINEA',
            'GIBRALTAR': 'SPAIN',
            'MARTINIQUE': 'FRANCE',
            'MARTINIQUE': 'FRANCE'
        }
        for k, v in name_match.items():
            if old_name == k:
                return v
        if not old_name in set(name_match):
            return old_name

    df['Location_Country'] = df.Location_Country.apply(rename_country)

    # subset df
    country_count_df = (
        df[df['Start Date'] > start]
        [df['Completion Date'] < end]
        # add criteria here
        [['Location_Country']]
        [(df['Location_Country'] != 'NAN') & (df['Location_Country'] != 'REPUBLIC OF')].  # the last criteria can be drop when we confirm what 'REPUBLIC OF' is
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
        title='Count of COVID-19 Trial by Country',
    )
    # the size of figure may need adjust
    geo_plot.update_layout(margin={"r": 0, "t": 50, "l": 0, "b": 0},
                           height=650,
                           width=950,
                           )

    return geo_plot

def get_state_plot(df=get_df(), gdf_state=get_gdf_state(), start=datetime(1900,1,1), end=datetime(2099,12,31)):
    """
    this function generate the plot to demonstrate how many trial in the each state in US
    Parameters
    ----------
    df : pandas.DataFrame
        df data frame
    gdf_state : pandas.DataFrame
        gdf data frame
    start: datetime
        the lower bound of time range for the plot
    end: datetime
        the upper bound of time range for the plot
    Returns
    ----------
    geo_state_plot:
        the plot demonstrate how many trial in the each state in US
    """
    state_count_df = (
        df[df['Start Date'] > start]
        [df['Completion Date'] < end]
        # add criteria here
        [df.Location_Country == 'UNITED STATES']
        [['Location_City_or_State']].
            assign(count=1).
            groupby(['Location_City_or_State']).
            agg('sum').
            sort_values('count', ascending=False)
    )
    state_count_df.index.name = 'State'

    # equip data with geo info
    geo_state_count_df = (
        gdf_state.merge(state_count_df, left_on='name', right_on='State', how='left').
            # fillna('No data', inplace = True).
            sort_values('count', ascending=False)
    )
    geo_state_count_df = geo_state_count_df.rename(columns={'name': 'State'})

    # Convert to geojson
    geo_state_count_json = json.loads(geo_state_count_df.to_json())

    geo_state_plot = px.choropleth_mapbox(
        data_frame=geo_state_count_df,
        geojson=geo_state_count_json,
        color='count',
        locations='State',
        featureidkey='properties.State',
        mapbox_style='carto-positron',  # can change background
        color_continuous_scale=px.colors.sequential.YlGnBu,  # make colorscale fix
        center={"lat": 38, "lon": -95},
        zoom=2.7,
        opacity=0.75,
        labels={"count": "Count of Trials"},
        title='Count of COVID-19 Trial in US by State',
    )
    geo_state_plot.update_layout(margin={"r": 0, "t": 50, "l": 0, "b": 0})

    return geo_state_plot

def get_location_plot(df=get_df(), start=datetime(1900,1,1), end=datetime(2099,12,31), n = 3, type = "treemap"):
    """
    this function generate the plot to demonstrate how many trial in the each location
    Parameters
    ----------
    df : pandas.DataFrame
        df data frame
    start: datetime
        the lower bound of time range for the plot
    end: datetime
        the upper bound of time range for the plot
    n : int
        the minimum number of trials of each insititution to be displayed
    type: str
        the type of the plot, "pie" or "treemap"
    Returns
    ----------
    plot:
        the plot demonstrate how many trial in the each location
    """
    country_city_inst_df = (
        df[df['Start Date'] > start]
        [df['Completion Date'] < end]
        [['Location_Country', 'Location_City_or_State', 'Location_Institution']]
        [df.Location_Country != 'NAN'].
            assign(count=1).
            groupby(['Location_Country', 'Location_City_or_State', 'Location_Institution']).
            agg('sum').
            reset_index()
    )
    country_city_inst_df["world"] = "World"
    country_city_inst_df["color"] = country_city_inst_df['Location_Country']
    country_city_inst_color = country_city_inst_df.groupby(['Location_Country']).agg({'color': 'count'})
    country_city_inst_df = (
        country_city_inst_df.
        drop(columns="color").
        merge(country_city_inst_color, left_on='Location_Country', right_on='Location_Country')
    )

    # n be the minimum number of trials of each insititution to be displayed
    country_city_inst_df = country_city_inst_df[country_city_inst_df['count'] >= n]

    if type == "pie":
        plot = px.sunburst(country_city_inst_df,
                                                 path=['Location_Country', 'Location_City_or_State',
                                                       'Location_Institution'],
                                                 values='count',
                                                 color='color',
                                                 color_continuous_scale='deep',
                                                 maxdepth=2)
    elif type == "treemap":
        plot = px.treemap(country_city_inst_df,
                          path=['world', 'Location_Country', 'Location_City_or_State',
                                'Location_Institution'],
                          color='color',
                          color_continuous_scale='deep',
                          maxdepth=2)
    return plot


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
    def cate_duration(duration):
        if duration < 1:
            return 'less then 1 month'
        elif duration <= 3:
            return '1 - 3 months'
        elif duration <= 6:
            return '4 - 6 months'
        elif duration <= 12:
            return '7 - 12 months'
        elif duration <= 24:
            return '1 - 2 years'
        elif duration <= 60:
            return '2 - 5 years'
        elif duration <= 120:
            return '5 - 10 years'
        else:
            return 'over 10 years'

    duration_df = df.Trial_Duration_Months.apply(cate_duration).value_counts().to_frame().reset_index()
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
    duration_df['Trial_Duration'] = duration_df['Trial_Duration'].astype('category')
    duration_df['Trial_Duration'].cat.reorder_categories(duration_order, inplace=True)
    duration_df.sort_values(sort_by, inplace=True)

    if type == "pie":
        plot = px.pie(duration_df,
                      values='count',
                      names='Trial_Duration',
                      color_discrete_sequence=px.colors.sequential.YlGnBu_r,
                      labels={"Trial_Duration": "Trial Duration",
                              "count": "Count of Trials",
                              },
                      title='COVID-19 Trial Duration')
    elif type == "bar":
        plot = px.bar(duration_df,
                      x='Trial_Duration',
                      y='count',
                      color='count',
                      color_continuous_scale='deep',
                      labels={'count': 'Count of Trials',
                              'Trial_Duration': 'Trial Duration'})

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

    def cate_eroll(enroll):
        if enroll < 10:
            return 'less then 10'
        elif enroll <= 50:
            return '11 - 50'
        elif enroll <= 100:
            return '51 - 100'
        elif enroll <= 200:
            return '101 - 200'
        elif enroll <= 500:
            return '201 - 500'
        elif enroll <= 1000:
            return '501 - 1000'
        elif enroll <= 5000:
            return '1001 - 5000'
        elif enroll <= 10000:
            return '5001 - 10000'
        else:
            return 'over 10000'

    enroll_df = df.Enrollment.apply(cate_eroll).value_counts().to_frame().reset_index()
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
    enroll_df['Enrollment'] = enroll_df['Enrollment'].astype('category')
    enroll_df['Enrollment'].cat.reorder_categories(enroll_order, inplace=True)
    enroll_df.sort_values(sort_by, inplace=True)

    if type == "pie":
        plot = px.pie(enroll_df,
                      values='count',
                      names='Enrollment',
                      color_discrete_sequence = px.colors.sequential.YlGnBu_r,
                      labels={"count": "Count of Trials"},
                      title='Number of Participants in COVID-19 Trial Project')
    elif type == "bar":
        plot = px.bar(enroll_df,
                      x='Enrollment',
                      y='count',
                      color='count',
                      color_continuous_scale = 'deep',
                      labels={'count':'Count of Trials'})
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
    Returns
    ----------
    plot:
        the plot of categorical variable
    """
    vars = {"Status": ('Status', 'Status of COVID-19 Trial Project'),
             "Age": ('Age', 'Participants Age of COVID-19 Trial Project'),
             "Phases": ('Phases', 'Phases of COVID-19 Trial Project')}

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
                      title=title_str)
        return plot

    def plot_bar(df, col, title_str):
        df = df[col].dropna().value_counts().to_frame().reset_index()
        df.columns = [col, 'count']
        df = df.sort_values('count', ascending=True)
        plot = px.bar(df,
                      x=col,
                      y='count',
                      color='count',
                      color_continuous_scale='deep',
                      labels={"count": "Count of Trials"},
                      title=title_str)
        return plot

    if type == "bar":
        plot = plot_bar(df, *var)
    elif type == "pie":
        plot = plot_pie(df, *var)

    return plot


# test #################################################################################################################

if __name__=="__main__":
    get_country_plot(center='europe').show()
    get_state_plot().show()
    get_location_plot(type="pie").show()
    get_trail_duration_plot(sort_by="count",type = "bar").show()
    get_enrollment_plot(sort_by='Enrollment').show()
    get_cat_plot(var="Age",type="pie").show()




