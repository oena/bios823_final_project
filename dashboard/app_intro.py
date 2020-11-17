import streamlit as st
from PIL import Image

def app():
    st.sidebar.subheader("Who we are?")
    st.sidebar.markdown(
    """
        Oana Enache (Biostatistics Department, Duke University School of Medicine) \n
        Yi Mi (Statistical Science Department, Duke University) \n
        Yue Han (Economics Department, Duke University)
    """
    )
    st.sidebar.subheader("[Link](https://github.com/oena/bios823_final_project) to GitHub")
    
    st.title('Welcome to COVID-19 Trial Dashboard!')
    st.header('Introduction about this dashboard')
    
    st.write("The overall goal of the dashboard is twofold; first, to provide a tool to explore COVID-19 related trials happening worldwide, and second, to provide a tool for people in the US to identify trials of interest to them by location. We have enabled this by providing: a display of trials happening worldwide ('Overall trials'), Trials happening in the United States ('US trials'), Clustering of Trials by different measures of similarity ('Trials Clustering'), and prediction about the activity level (open or not) of available trials ('Activeness predicting').")
    
    st.header('About the data')
    st.write("This data is derived from [all COVID-19 related results on clinicaltrials.gov](https://clinicaltrials.gov/ct2/results?cond=COVID-19).")  
    
   
