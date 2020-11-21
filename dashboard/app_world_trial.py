import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely import wkt
import numpy as np
from datetime import datetime
import json
from dateutil.relativedelta import relativedelta
import viz

def app():
    # methods to load and change data
    @st.cache(allow_output_mutation=True)
    def load_datasets():
        return pd.read_csv("https://media.githubusercontent.com/media/oena/bios823_final_project/master/dashboard/dashboard_data/cleaned_data_for_viz.tsv", sep="\t")
        
    def filter_data_for_map(df):
        country_count_df = (
            df[['Location_Country']]
            [df['Location_Country'] != 'NAN'].
            assign(count=1).
            groupby(['Location_Country']).
            agg('sum').
            sort_values('count', ascending=False).
            reset_index()
        )
        return country_count_df
    
    @st.cache(allow_output_mutation=True)
    def load_geo_data():
        df =pd.read_csv("https://media.githubusercontent.com/media/oena/bios823_final_project/master/dashboard/dashboard_data/cleaned_data_for_map_with_geo.tsv",sep="\t")
        df['geometry'] = df['geometry'].apply(wkt.loads)
        gdf = gpd.GeoDataFrame(df, geometry='geometry')
        return gdf
    
    def filter_dataset(df, start, end, study_type):
        df = (
            df[df['Start Date'].apply(pd.to_datetime) > pd.to_datetime(start)]
            [df['Completion Date'].apply(pd.to_datetime) < pd.to_datetime(end)]
        )
        if study_type=="All":
            return df
        else:
            return df[df["Study Type"]==study_type]
        
    # load in data
    df_origin = load_datasets()
    df = df_origin.copy()

    # sidebar control
    st.sidebar.subheader("Choose time interval:")
    start = st.sidebar.date_input("Start from:",value=datetime(2020,1,1),min_value=datetime(2000,1,1),max_value=datetime(2099,12,31))
    end = st.sidebar.date_input("To:",value=start+relativedelta(years=5),min_value=start,max_value=datetime(2099,12,31))
    
    st.sidebar.subheader("Choose trial study type:")
    study_type = st.sidebar.selectbox("Study type of trial:",
                                     options = ["All",
                                     "INTERVENTIONAL",
                                     "OBSERVATIONAL"])

    st.sidebar.subheader("Bar/Pie chart options:")
    attribute_display = st.sidebar.selectbox("Choose attribution to display:", options=["Status", "Phases", "Duration", "Funded Bys", "Enrollment", "Age"])

    if attribute_display == "Duration" or attribute_display == "Enrollment":
        sort_by = st.sidebar.radio("Bar chart X axis's order:", options=["Count of trial's order", "Attribute's order"])
    
    # filter data
    df = filter_dataset(df, start, end, study_type)
    map_data = filter_data_for_map(df)
    gdf = load_geo_data().drop(columns="count").merge(map_data, left_on='ADMIN', right_on='Location_Country', how='left').sort_values('count', ascending=False)
    
    # title
    st.title("How COVID-19 trials going on all over the world?")

    total_trials = df.shape[0]
    st.header(f'Total trials of {study_type.lower()} study type(s) from {start} to {end}: **{total_trials}**')
    
    with st.beta_expander("Click here to expand more details about this page"):
        st.subheader("Instruction about this page:")
        st.markdown(
            """
            In this page you can explore the how many clinical trials are going on all over the world in different time interval and for different study types. \n
            After choosing the time interval and study type, the map plot will show you how many trials in each countries by your filtering criteria, and you can easily find the region you are interested in by choosing where to centered at. \n
            Below are bar and pie chart will show the count/proportion of trials for different categories in each attribution. You can display the attribution you are interested in by choosing the options in sidebar.
            """
        )

    # main plots
    ## map plot
    st.subheader('Map plot for count of COVID-19 trials by country')
    with st.beta_container():

        c1, c2 = st.beta_columns([8,2])

        c2.markdown("**Change map display:**")

        def options_show(x):
            x = x.title().replace("_", " ")
            return x

        radio_display = c2.radio("Centered at:",
                                options=[
                                    "world",
                                    "europe",
                                    "north_america",
                                    "south_america",
                                    "africa",
                                    "asia",
                                    "oceania"
                                    ],
                                    format_func=options_show)
                                    
        advanced_select = c2.checkbox("Select country")
        if advanced_select:
            map_data.shape[0]
            number_to_display = c2.number_input("Select top countires to display", min_value = 1, max_value = map_data.shape[0], value = 5, step = 1)
            countries = c2.multiselect("Choose the countries you interested in:", map_data.head(number_to_display)
    .Location_Country.to_list(), default = map_data.head(number_to_display)
    .Location_Country.to_list())
    
            countries_select_df = [x in countries for x in df.Location_Country]
            df["if_select"] = countries_select_df
            countries_select_map_data = [x in countries for x in map_data.Location_Country]
            map_data["if_select"] = countries_select_map_data
            countries_select_gdf = [x in countries for x in gdf.ADMIN]
            gdf["if_select"] = countries_select_gdf
            
            df = df[df["if_select"] == True]

            map_data = map_data[map_data["if_select"] == True].head(number_to_display)

            gdf = gdf[gdf["if_select"] == True].head(number_to_display)
                
        show_table = c2.checkbox("Show table")
        
        c1.plotly_chart(viz.get_country_plot(map_data, gdf, center=radio_display), use_container_width=True)
        c1.write(f'Total trials in selected countries: **{sum(map_data["count"])}**')
        c1.write("*\*Note: total trials in all countries may differ from total trials in all records since some trial records don't have country info.*")
        if show_table:
            if "if_select" in map_data.columns:
                c1.write(map_data.drop(columns = "if_select"))
            else:
                c1.write(map_data)
    
    
    ## bar and pie plot
    st.subheader(f'Bar and pie chart for count of COVID-19 trials by **{attribute_display.lower()}** attribution')
    with st.beta_container():

        c3, c4 = st.beta_columns([5,5])

        if attribute_display == "Duration":
            if sort_by == "Count of trial's order":
                sort_by = "count"
            else:
                sort_by = "Trial_Duration"
            # bar plot
            bar_plot = viz.get_trail_duration_plot(df=df, sort_by=sort_by, type="bar")
            # pie plot
            pie_plot = viz.get_trail_duration_plot(df=df, sort_by=sort_by, type="pie")

        elif attribute_display == "Enrollment":
            if sort_by == "Count of trial's order":
                sort_by = "count"
            else:
                sort_by = "Enrollment"
            # bar plot
            bar_plot = viz.get_enrollment_plot(df=df, sort_by=sort_by, type="bar")
            # pie plot
            pie_plot = viz.get_enrollment_plot(df=df, sort_by=sort_by, type="pie")

        else:
            # bar plot
            bar_plot = viz.get_cat_plot(df=df, var=attribute_display, type="bar")
            # pie plot
            pie_plot = viz.get_cat_plot(df=df, var=attribute_display, type="pie")

            
        bar_plot.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0},
                               height=400,
                               plot_bgcolor='rgba(0,0,0,0)')
        
        c3.plotly_chart(bar_plot, use_container_width=True)
        
        pie_plot.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0},
                               height=400,
                               plot_bgcolor='rgba(0,0,0,0)')
        c4.plotly_chart(pie_plot, use_container_width=True)
