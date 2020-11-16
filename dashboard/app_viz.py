import streamlit as st
import pandas as pd
from datetime import datetime
import json
from dateutil.relativedelta import relativedelta
import viz

def app():
    # methods to load and change data
    @st.cache()
    def load_datasets():
        return pd.read_csv("dashboard/cleaned_data_for_viz.tsv", sep="\t")
    
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
    gdf = viz.get_gdf()

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

    df = filter_dataset(df, start, end, study_type)
    total_trials = df.shape[0]
    
    # title
    st.title("How COVID-19 trials going on all over the world?")
    
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

        c1.plotly_chart(viz.get_country_plot(*viz.get_data_for_map(df, gdf), center=radio_display), use_container_width=True)
    
    st.write("")
    
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

            
        bar_plot.update_layout(margin={"r": 0, "t": 10, "l": 0, "b": 0},
                               height=400,
                               plot_bgcolor='rgba(0,0,0,0)')
        
        c3.plotly_chart(bar_plot, use_container_width=True)
        
        pie_plot.update_layout(margin={"r": 0, "t": 10, "l": 0, "b": 0},
                               height=400,
                               plot_bgcolor='rgba(0,0,0,0)')
        c4.plotly_chart(pie_plot, use_container_width=True)
