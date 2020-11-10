import streamlit as st
import pandas as pd
import plotly.express as px

# Page configuration -- set to wide
st.set_page_config(layout="wide")

# Methods to load and change data
@st.cache()
def load_datasets():
    # All US clinical trials
    data_df = pd.read_csv("data/cleaned_us_covid_studies_with_geo_092020.tsv", sep="\t")
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
                       state_selection,
                       intervention_selection,
                       drug_selection,
                       map_display,
                   output_type):
    # Filter if needed
    if state_selection != "All available states":
        all_us_data = all_us_data[all_us_data["Location_City_or_State"] == state_selection]
    if intervention_selection != "All available interventions":
        all_us_data = all_us_data[all_us_data["Intervention Type"] == intervention_selection]
    if drug_selection != "All available drugs & biologics":
        all_us_data = all_us_data[all_us_data["Drug Type"] == drug_selection]

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
        elif map_display == "Trial statuses":
            out_df = pd.DataFrame(all_us_data.groupby.groupby(["Location_Institution", "lat", "lon"])["Status"].agg(["unique"]))
            out_df.reset_index(inplace=True)
            out_df.columns = ['Institution', 'Latitude', 'Longitude', "Trial statuses"]
        return out_df

# Load data initially
data_load_state = st.text("Loading data...")
us_study_data = load_datasets()
filter_options = load_filtering_options(us_study_data)
data_load_state.text("")

# Page title
st.title("What kinds of COVID-19 trials are happening in the US?")
st.header("An interactive tool to explore ongoing clinical trial efforts")
with st.beta_expander("Click here to expand more details about this dashboard"):
    st.subheader("About this data:")
    st.markdown("There are two primary sources for this dashboard: \n "
                "1. [The US government's clinical_trials.gov](https://clinicaltrials.gov/ct2/results?cond=COVID-19), which "
                "contains all registered trial information. \n "
                "2. [The Atlantic's COVID-tracking API](https://covidtracking.com/data/api), which is used to get up to date"
                "information on hospitalizations and ongoing cases.")
    st.write("")
    st.subheader("Some potential caveats to note:")
    st.markdown("1. Adding geospatial data to some study locations was not possible in an automated fashion, "
                "so they are not included in the plot below. \n "
                "2. Geospatial data was added automatically by institute (mostly hospital) location name using `geopy`, "
                "so it may not be accurate for all locations.")

# Sidebar to switch between study locations and latest covid rates
st.sidebar.subheader("Filter trial information:")
state_value = st.sidebar.selectbox("Find trials by state:",
                                   filter_options["by_state"])
intervention_type = st.sidebar.selectbox("Find trials by intervention type:",
                                         filter_options["by_intervention_type"])
intervention = st.sidebar.selectbox("Find trials by drugs/biologics being studied: ",
                                    filter_options["by_drug"])
show_data_table = st.sidebar.checkbox("Show study information fulfilling above criteria")


# Main plot

with st.beta_container():
    # Map title
    st.subheader("Count of ongoing COVID clinical trials by institute")
    st.write("As of 09/20/20")

    # Map layout
    c1, c2 = st.beta_columns([5,2])

    # Select box for map -- changes displayed colors on map
    c2.markdown("**Change map display:**")
    radio_display = c2.radio("Choose one of:",
                    options=["Number of ongoing trials",
                             "Number of interventions",
                             "Trial statuses",
                             "Number of COVID hospitalizations",
                             "Predicted COVID status (are locations getting better or getting worse?)"])

    # Evaluate which color to display

    # Plot map
    count_df= filter_dataset(us_study_data,
                              state_value,
                  intervention_type,
                  intervention,
                  radio_display,
                   "count")
    count_map = px.scatter_mapbox(count_df,
                            lat="Latitude",
                            lon="Longitude",
                            color=radio_display,
                            size=radio_display,
                            color_discrete_sequence=px.colors.sequential.Plasma_r,
                            hover_name="Institution",
                            mapbox_style="light",
                            zoom=2)
    count_map.update_layout(width=1100, height=600)
    c1.plotly_chart(count_map)

# Supplementary plots
# TODO -- Yue to add, hopefully
with st.beta_container():
    st.subheader("More trial details: ")
    p1, p2, p3 = st.beta_columns((1,1,1))

    p1.markdown("**Plot 1 title**")

    p2.markdown("**Plot 2 title**")

    p3.markdown("**Plot 3 title**")

# Data table of studies
if show_data_table:
    with st.beta_container():
        st.subheader("Summary table of key trial information")
        filtered_data = filter_dataset(us_study_data,
                              state_value,
                  intervention_type,
                  intervention,
                  radio_display,
                  "data")
        st.write(filtered_data)
