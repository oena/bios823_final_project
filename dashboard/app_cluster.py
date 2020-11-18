import streamlit as st
import pandas as pd
from kmodes.kmodes import KModes
import plotly.express as px
import cluster

def app():
    # basic setting
    basic_info_cols = ["Status", "Phases", "Study Type", "Study Results",          "Trial_Duration_Category",
                       "INDUSTRY", "NIH", "OTHER FUND SOURCE", "U.S. FED"]
    participants_info_cols = ["Age", "Gender","Enrollment_Category"]
    study_design_cols = ["ALLOCATION", "INTERVENTION MODEL", "PRIMARY PURPOSE",
                        "OBSERVATIONAL MODEL", "TIME PERSPECTIVE",
                        "PARTICIPANT", "CARE PROVIDER","INVESTIGATOR", "OUTCOMES ASSESSOR"]
    intervention_cols = ["DRUG", "PROCEDURE", "OTHER INTERVENTIONS TYPE", "DEVICE", "BIOLOGICAL", "DIAGNOSTIC TEST",
                        "DIETARY SUPPLEMENT", "GENETIC", "COMBINATION PRODUCT", "BEHAVIORAL", "RADIATION"]

    feature_set = {
        "basic info" : basic_info_cols,
        "pariticpants" : participants_info_cols,
        "study design" : study_design_cols,
        "intervention" : intervention_cols
    }
    
    
    # load data
    df = cluster.get_data_for_cluster()
    
    st.sidebar.subheader("Cluster options:")
    scope = st.sidebar.selectbox("Choose scope:", options = ["Worldwide", "US"])
    def attr_show(x):
        return x.title()
    attr = st.sidebar.selectbox("Choose by which set of attributions to cluster:",
                         options = [
                            "basic info",
                            "pariticpants",
                            "study design",
                            "intervention",
                         ],
                         format_func=attr_show)
    n_clusters = st.sidebar.selectbox("Choose the number of clusters:",
                         options = [
                            "Auto",
                            3,
                            4,
                            5,
                            6,
                            7
                         ])
    st.sidebar.subheader("Display options:")
    display = st.sidebar.selectbox("Choose by which set of attributions to cluster:",
                         options = feature_set[attr])
    show_centroid = st.sidebar.checkbox("Show centroid of each cluster")
    show_cluster_table = st.sidebar.checkbox("Show trials with preidcted cluster")
    
    # filter df
    if scope == "US":
        df = df[df["Location_Country"] == "UNITED STATES OF AMERICA"]
    df_feature = cluster.choose_feature(df=df, feature_type=attr)
    
    # implement cluster
    if n_clusters == "Auto":
        km = cluster.get_cluster(df=df_feature)
    else:
        km = KModes(n_clusters=n_clusters, init = "Huang", n_init = 1, verbose=0, random_state=1)
    df_with_cluster, cluster_centroids, cluster_labels = cluster.get_clustered_data(km=km, df=df_feature)
    
    # page layout
    st.title('Can we divide trials into several groups?')
    
    st.header(
        """
        We use K-Mode algorithm to classify COVID-19 clinical trials into different groups.
        """
    )
    
    with st.beta_expander("Click here to expand more details about our cluster model"):
        st.subheader("K-Mode cluster introduction:")
        st.markdown(
            """
            We use K-Mode algorithm for our cluster model beacuse our dataset is fully composed of catgorical data, and we cannot apply K-Mean since "distance" is meaningless for categorical dataset. \n
            What K-Mode do is basically the same as K-Mean, except it choose the mode in each feature as the center instead of mean. For example, if our dataset is students from different contries, for the initial cluster, in cluster 1, 5 students come from US, 3 from China, 2 from Japan, so the centroid of this cluster is US. The rest steps of K-Mode are exactly the same as K-mean. \n
            To implement this algorithm, we use the package `kmodes`, and you can refer to this [site](https://pypi.org/project/kmodes/) for more information.
            """
        )
    # plot
    st.subheader(f'Count of trial for each catergory of {display} attribution in each cluster')
    plot = cluster.plot_cluster(df_with_cluster=df_with_cluster, feature=display)
    plot.update_layout(margin={"r": 0, "t": 10, "l": 0, "b": 0},
                               height=400,
                               plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(plot, use_container_width=True)
    
    # centroids
    if show_centroid:
        st.subheader("Centroid of each cluster")
        st.write(cluster_centroids)
    
    # cluster table
    if show_cluster_table:
        st.subheader("Table of trials with preidcted cluster")
        st.write(df_with_cluster)
    
    

