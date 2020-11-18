import streamlit as st
import app_intro
import app_viz
import app_us_trial
import app_cluster
import app_predict_activeness

# Page configuration -- set to wide
st.set_page_config(layout="wide")

PAGES = {
    "Homepage": app_intro,
    "Overall trials": app_world_trials,
    "US trials": app_us_trial,
    "Trials clustering": app_cluster,
    "Trials opening status" : app_predict_activeness
}
st.sidebar.title('Navigation')
selection = st.sidebar.selectbox("Go to page:", list(PAGES.keys()))
page = PAGES[selection]
page.app()
