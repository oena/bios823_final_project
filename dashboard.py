import streamlit as st
import pandas as pd
import plotly.express as px

# Public key for mapbox access
px.set_mapbox_access_token("pk.eyJ1Ijoib2VuYWNoZSIsImEiOiJjazM2NWVwcmUxZnc3M2JvcXVvbjJiN2dpIn0.WZidyL9W3mlaLbM0TvAVXQ")

# Page configuration -- set to wide
st.set_page_config(layout="wide")

@st.cache()
def load_datasets():
    # All US clinical trials
    data_df = pd.read_csv("data/cleaned_us_covid_studies_with_geo_092020.tsv", sep="\t")
    all_us_data = data_df.dropna()

    # Count of clinical trials by institution, for map
    studies_per_location = pd.DataFrame(all_us_data.groupby(["Location_Institution", "lat", "lon"])["NCT Number"].nunique())
    studies_per_location.reset_index(inplace=True)
    studies_per_location.columns = ['Institution', 'Latitude', 'Longitude', "Number of trials"]

    return all_us_data, studies_per_location

@st.cache()
def load_filtering_options(all_us_data):
    filter_options = {}

    # states represented
    states_list = list(all_us_data["Location_City_or_State"].unique())
    states_list.sort()
    states_list.insert(0, "All available states")
    filter_options["by_state"] = states_list

    # interventions represented
    intervention_type_list = list(set([i.split(": ")[0] for i in list(all_us_data["Interventions"].unique())]))
    intervention_type_list.sort()
    intervention_type_list.insert(0, "All available interventions")
    filter_options["by_intervention_type"] = intervention_type_list

    # drugs represented
    drug_list = [i.split(": ")[1] for i in list(all_us_data["Interventions"].unique()) if i.split(": ")[0] in ["DRUG", "BIOLOGICAL"]]
    drug_list.sort()
    drug_list.insert(0, "All available drugs & biologics")
    filter_options["by_drug"] = drug_list

    return filter_options

# Load data
data_load_state = st.text("Loading data...")
us_study_data, studies_per_location = load_datasets()
filter_options = load_filtering_options(us_study_data)
data_load_state.text("")

# Page title
st.title("What kinds of COVID-19 trials are happening in the US?")
st.header("An interactive tool to explore ongoing trial efforts")
with st.beta_expander("Expand here for more details"):
    st.write("Data from clinicaltrials.gov of studies with keyword `COVID-19`. Note that (1) adding geospatial data to some study"
             "locations was not possible in an automated fashion, so they are not included in the plot below; also, (2) Geospatial"
             "data was added automatically by location name using `geopy`, so it may not be accurate for all locations.")

# Sidebar to switch between study locations and latest covid rates
add_selectbox = st.sidebar.selectbox(
    "Display on map:",
    ("Number of trials", "Change in deaths this week", "Change in tests this week")
)
state_value = st.sidebar.selectbox("Find trials by state:",
                                   filter_options["by_state"])
intervention_type = st.sidebar.selectbox("Find trials by intervention type:",
                                         filter_options["by_intervention_type"])
intervention = st.sidebar.selectbox("Find trials by drugs/biologics being studied: ",
                                    filter_options["by_drug"])
st.sidebar.checkbox("Show study information fulfilling above criteria")


# Main plot
with st.beta_container():
    st.subheader("Count of ongoing COVID clinical trials by institute, as of 9/20/20")
    count_map = px.scatter_mapbox(studies_per_location,
                            lat="Latitude",
                            lon="Longitude",
                            color="Number of trials",
                            size="Number of trials",
                            color_discrete_sequence=px.colors.sequential.Plasma_r,
                            hover_name="Institution",
                            mapbox_style="light",
                            zoom=2)
    count_map.update_layout(width=1100, height=600)
    st.plotly_chart(count_map)

# Supplementary plots
# TODO -- Yue to add
p1, p2, p3 = st.beta_columns((1,1,1))

p1.subheader("Plot 1 Sub-header")

p2.subheader("Plot 2 Sub-header")

p3.subheader("Plot 3 Sub-header")

# Data table of studies
