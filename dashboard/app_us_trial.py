import streamlit as st
import pandas as pd
import plotly.express as px
import base64

def app():
    px.set_mapbox_access_token("pk.eyJ1Ijoib2VuYWNoZSIsImEiOiJjazM2NWVwcmUxZnc3M2JvcXVvbjJiN2dpIn0.WZidyL9W3mlaLbM0TvAVXQ")

    # Methods to load and change data
    @st.cache()
    def load_datasets():
        # All US clinical trials
        data_df = pd.read_csv("https://media.githubusercontent.com/media/oena/bios823_final_project/master/dashboard/dashboard_data/cleaned_us_covid_studies_with_geo_092020.tsv", sep="\t")
        all_us_data = data_df.dropna()
        return all_us_data

    @st.cache()
    def load_filtering_options(all_us_data):
        filter_options = {}

        # states represented
        states_list = list(all_us_data["Location_City_or_State"].unique())
        states_list.sort()
        states_list.insert(0, "All available states")
        filter_options["by_state"] = states_list

        # Phase
        phase_list = list(all_us_data["Phases"].unique())
        phase_list.sort()
        phase_list.insert(0, "All phases")
        filter_options["by_phase"] = phase_list

        # interventions represented
        intervention_type_list = list(all_us_data["Intervention Type"].unique())
        intervention_type_list.sort()
        intervention_type_list.insert(0, "All available interventions")
        filter_options["by_intervention_type"] = intervention_type_list

        # drugs represented
        drug_list = [i.split(": ")[1] for i in list(all_us_data["Interventions"].unique()) if i.split(": ")[0] in ["DRUG", "BIOLOGICAL"]]
        drug_list.sort()
        drug_list.insert(0, "All available drugs & biologics")
        filter_options["by_drug"] = drug_list

        return filter_options

    def filter_dataset(all_us_data,
                           drug_selection,
                           map_display,
                       output_type):
        # Filter if needed
        if drug_selection != "All available drugs & biologics":
            all_us_data = all_us_data[all_us_data["Drug Type"] == drug_selection]
            print(all_us_data.shape)

        if output_type == "data":
            return all_us_data
        else:
            # Count of clinical trials by institution, for map
            if map_display == "Number of ongoing trials":
                out_df = pd.DataFrame(all_us_data.groupby(["Location_Institution", "lat", "lon"])["NCT Number"].nunique())
                out_df.reset_index(inplace=True)
                out_df.columns = ['Institution', 'Latitude', 'Longitude', "Number of ongoing trials"]
            elif map_display == "Number of interventions":
                out_df = pd.DataFrame(all_us_data.groupby(["Location_Institution", "lat", "lon"])["Interventions"].nunique())
                out_df.reset_index(inplace=True)
                out_df.columns = ['Institution', 'Latitude', 'Longitude', "Number of interventions"]
            elif map_display == "Trial enrollment status":
                out_df = pd.DataFrame(all_us_data.groupby(["Location_Institution", "lat", "lon", "Enrollment"])["Status"].agg(["unique"]))
                out_df.reset_index(inplace=True)
                out_df.columns = ['Institution', 'Latitude', 'Longitude', "Enrollment", "Trial enrollment status"]
                out_df["Trial enrollment status"] = [i[0] for i in out_df["Trial enrollment status"].values]
            return out_df

    def download_link(object_to_download, download_filename, download_link_text):
        """
        Generates a link to download the given object_to_download.

        object_to_download (str, pd.DataFrame):  The object to be downloaded.
        download_filename (str): filename and extension of file. e.g. mydata.csv, some_txt_output.txt
        download_link_text (str): Text to display for download link.

        Examples:
        download_link(YOUR_DF, 'YOUR_DF.csv', 'Click here to download data!')
        download_link(YOUR_STRING, 'YOUR_STRING.txt', 'Click here to download your text!')

        """
        if isinstance(object_to_download,pd.DataFrame):
            object_to_download = object_to_download.to_csv(index=False)

        # some strings <-> bytes conversions necessary here
        b64 = base64.b64encode(object_to_download.encode()).decode()

        return f'<a href="data:file/txt;base64,{b64}" download="{download_filename}">{download_link_text}</a>'

    # Load data initially
    data_load_state = st.text("Loading data...")
    us_study_data = load_datasets()
    filter_options = load_filtering_options(us_study_data)
    data_load_state.text("")

    # Page title
    st.title("What kinds of COVID-19 trials are happening in the US?")
    st.header("Explore ongoing clinical trial efforts in US")

    with st.beta_expander("Click here to expand more details about this page"):
        st.subheader("Some potential caveats to note:")
        st.markdown("- Adding geospatial data to some study locations was not possible in an automated fashion, "
                    "so they are not included in the plot below. \n "
                    "- Geospatial data was added automatically by institute (mostly hospital) location name using `geopy`, "
                    "so it may not be accurate for all locations.")

    # Sidebar to switch between study locations and latest covid rates
    st.sidebar.subheader("Filter trial information:")

    state_value = st.sidebar.selectbox("Filter trials by state:",
                                       filter_options["by_state"])
    if state_value != "All available states":
        us_study_data = us_study_data[us_study_data["Location_City_or_State"] == state_value]
        filter_options = load_filtering_options(us_study_data)

    phase_value = st.sidebar.selectbox("Filter trials by phase:",
                                       filter_options["by_phase"])
    if phase_value != "All phases":
        us_study_data = us_study_data[us_study_data["Phases"] == phase_value]
        filter_options = load_filtering_options(us_study_data)

    intervention_type = st.sidebar.selectbox("Find trials by intervention type:",
                                             filter_options["by_intervention_type"])
    if intervention_type != "All available interventions":
        us_study_data = us_study_data[us_study_data["Intervention Type"] == intervention_type]
        filter_options = load_filtering_options(us_study_data)

    intervention = st.sidebar.selectbox("Find trials by drugs/biologics being studied: ",
                                        filter_options["by_drug"])
    st.sidebar.write("Note. A biologic (aka biological) is a drug made from living organisms (or components thereof).")

    show_data_table = st.sidebar.checkbox("Show study information fulfilling above criteria")


    # Main plot

    with st.beta_container():
        # Map title
        st.subheader("Count of ongoing COVID clinical trials by institute")

        # Map layout
        c1, c2 = st.beta_columns([8,2])

        # Select box for map -- changes displayed colors on map
        c2.markdown("**Change map display:**")
        radio_display = c2.radio("Choose one of:",
                        options=["Number of ongoing trials",
                                 "Number of interventions",
                                 "Trial enrollment status"])

        # Plot map
        filtered_count_df = filter_dataset(us_study_data,
                      intervention,
                      radio_display,
                       "count")
        # Color palette type needs to change depending on what's displayed
        if radio_display == "Trial enrollment status":
            count_map = px.scatter_mapbox(filtered_count_df,
                            lat="Latitude",
                            lon="Longitude",
                            color=radio_display,
                            size="Enrollment",
                            hover_name="Institution",
                            mapbox_style="light",
                            center={"lat": 38, "lon": -95},
                            zoom=2)
        else:
            count_map = px.scatter_mapbox(filtered_count_df,
                                    lat="Latitude",
                                    lon="Longitude",
                                    color=radio_display,
                                    size=radio_display,
                                    #color_discrete_sequence=color_palette,
                                    hover_name="Institution",
                                    mapbox_style="light",
                                    center={"lat": 38, "lon": -95},
                                    zoom=2)
        count_map.update_layout(width=1100, height=600)
        c1.plotly_chart(count_map, use_container_width=True)

    # Data table of studies
    if show_data_table:
        with st.beta_container():
            st.subheader("Summary table of key trial information")
            cols_to_keep = ["NCT Number",
                            "Title",
                            "Phases",
                            "Status",
                            "Enrollment",
                            "Location_City_or_State",
                            "Location_Institution",
                            "Address",
                            "URL"]
            filtered_data = filter_dataset(us_study_data,
                      intervention,
                      radio_display,
                      "data")
            filtered_data_display = filtered_data[cols_to_keep].drop_duplicates()
            st.write(filtered_data_display)
            if st.button('Download Dataframe as CSV'):
                tmp_download_link = download_link(filtered_data_display, 'covid_trials_information.csv', 'Click here to download your data!')
                st.markdown(tmp_download_link, unsafe_allow_html=True)
