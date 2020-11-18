from datetime import datetime
from kmodes.kmodes import KModes

import pandas as pd
import numpy as np
import sqlite3

import plotly.express as px

def get_data_for_cluster():
    return pd.read_csv("https://media.githubusercontent.com/media/oena/bios823_final_project/master/dashboard/dashboard_data/cleaned_data_for_cluster.tsv", sep="\t",index_col=0)

def choose_feature(df=get_data_for_cluster(), feature_type="basic info"):
    """
    this function do cluster for trials according to specified cols
    Parameters
    ----------
    df : pandas.DataFrame
        data frame of features that used to cluster
    feature_type: str
        which set of features we what to ues
    Returns
    ----------
    df_:
        subseted data frame with the features we interested in
    """
    basic_info_cols = ["Status", "Phases", "Study Type", "Study Results",           "Trial_Duration_Category",
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

    df_ = df[feature_set[feature_type]]

    return df_

def get_cluster(df=choose_feature()):
    """
    this function choose the best number of cluster and return an cluster algo
    Parameters
    ----------
    df : pandas.DataFrame
        data frame of features that used to cluster
    Returns
    ----------
    km:
        the cluster algo with best number of cluster
    """
    # choosing best number of cluster
    hyperparams = {
    "n_clusters":range(2,11),
    "init":["Huang","Cao"]
    }

    para_cost = {}

    for init in hyperparams["init"]:
        cost = []
        for n in hyperparams["n_clusters"]:
            km = KModes(n_clusters=n, init = init, n_init = 1, verbose=0, random_state=1)
            km.fit_predict(df)
            cost.append(km.cost_)
        cost_decrease_ratio = [(cost[n-1] - cost[n])/cost[n-1] if n > 0 else 1 for n, k in enumerate(cost)]
        if_decrease_slow = [1 if cost_decrease_ratio[n] < 0.02 else 0 for n, k in enumerate(cost_decrease_ratio)]
        if 1 in if_decrease_slow:
            idx = np.argwhere(np.array(if_decrease_slow)==1).min() - 1
        else:
            idx = len(if_decrease_slow) - 1
        k = list(hyperparams["n_clusters"])[idx]
        para_cost[(init, k)] = cost[idx]

    best_para = min(para_cost,key=para_cost.get)
    best_para_dict = {"n_clusters":best_para[1], "init":best_para[0]}

    # fit model
    km = KModes(**best_para_dict, n_init = 1, random_state=1, verbose=0)

    return km
    
def get_clustered_data(km=get_cluster(), df=choose_feature()):
    """
    this function predict cluster of data and combine it with origin df
    Parameters
    ----------
    km
        a kmode cluster algo
    df : pandas.DataFrame
        data frame of features that used to cluster
    Returns
    ----------
    df_with_cluster:
        the df with predicted cluster
    cluster_centroids
    cluster_labels
    """
    fit_clusters = km.fit_predict(df)
    cluster_centroids = pd.DataFrame(km.cluster_centroids_)
    cluster_centroids.columns = df.columns
    
    cluster_labels = pd.DataFrame(fit_clusters)
    cluster_labels.columns = ['Cluster Predicted']
    df_with_cluster = df.reset_index().merge(cluster_labels, left_index=True, right_index=True).set_index("NCT Number")
    return df_with_cluster, cluster_centroids, cluster_labels

def plot_cluster(df_with_cluster=get_clustered_data()[0], feature="Study Type"):
    """
    this function plot how categories distributed in each cluster for a specific feature
    Parameters
    ----------
    df_with_cluster:
        the df with predicted cluster
    feature: str
        which feature to display, this feature must be in df
    Returns
    ----------
    plot:
        the plot demonstrate how category distributed in each cluster for a specific feature
    """
    df_count_cluster = df_with_cluster.assign(count=1).groupby(['Cluster Predicted',feature]).agg({"count":'count'}).reset_index()

    plot = px.bar(df_count_cluster,
                  x="Cluster Predicted",
                  y="count",
                  color=feature,
                  color_discrete_sequence=px.colors.qualitative.Set3,
                  barmode='group')

    return plot

# test 
if __name__=="__main__":
    plot_cluster(feature="Trial_Duration_Category").show()

