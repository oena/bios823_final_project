from datetime import datetime
from kmodes.kmodes import KModes

import pandas as pd
import numpy as np
import sqlite3

import plotly.express as px

def get_data_for_cluster():
    """
    this function return a merged df for cluster
    """
    # load in data
    conn = sqlite3.connect('covid_trials.db')
    trial_info=pd.read_sql("select * from trial_info", con = conn)
    study_designs=pd.read_sql("select * from study_designs", con = conn)
    interventions=pd.read_sql("select * from interventions", con = conn)
    funded_bys=pd.read_sql("select * from funded_bys", con = conn)
    conn.close()

    # trial info
    df = trial_info.copy()

    ## age
    df['Age'] = df.Age.str.extract(r'[(](.*?)[)]')

    ## date
    date_columns = ['Start Date',                       
                    'Completion Date',
                    'First Posted',
                    'Last Update Posted' ]

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

    ## categorize numeric variables
    df["Trial_Duration_Category"] = pd.cut(df.Trial_Duration_Months,
                                        [-float('inf'),0,3,6,12,24,60,120,float('inf')],
                                        labels=['less then 1 month','1 - 3 months','4 - 6 months','7 - 12 months',
                                                '1 - 2 years','2 - 5 years','5 - 10 years','over 10 years'])
    df["Enrollment_Category"] = pd.cut(df.Enrollment,
                                    [-float('inf'),9,50,100,200,500,1000,5000,10000,float('inf')],
                                    labels=['less then 10','11 - 50','51 - 100','101 - 200',
                                            '201 - 500','501 - 1000','1001 - 5000','5001 - 10000','over 10000'])

    ## clean study type variable
    df["Study Type"] = (
        df["Study Type"].
        replace({"TREATMENT IND/PROTOCOL":"EXPANDED ACCESS",
                "INTERMEDIATE-SIZE POPULATION":"EXPANDED ACCESS",})
        .replace(regex={r'EXPANDED ACCESS:.*':"EXPANDED ACCESS"})
    )

    # mask
    mask_cols = ["PARTICIPANT", "CARE PROVIDER", "INVESTIGATOR", "OUTCOMES ASSESSOR"]
    mask = study_designs[["NCT Number", "MASKING"]].replace({np.nan:""})
    for col in mask_cols:
        mask[col] = [col in mask.MASKING[i] for i in range(mask.MASKING.size)]
    mask.drop(columns="MASKING", inplace=True)
    mask = mask.set_index("NCT Number")

    # study design
    study_designs_ = study_designs.drop(columns="MASKING")
    study_designs_ = study_designs_.set_index("NCT Number")

    # interventions
    interventions_type = interventions
    interventions_type.iloc[:,1:] = (interventions.replace({np.nan:0}) == 0).iloc[:,1:]
    interventions_type = interventions_type.set_index("NCT Number")
    interventions_type = interventions_type.rename(columns={"OTHER":'OTHER INTERVENTIONS TYPE'})

    # fund bys
    funded_bys_ = (
    funded_bys.drop(columns = "index").
    assign(value=True).
    drop_duplicates().
    pivot(index='NCT Number', columns='Funded Bys', values='value').
    replace({np.nan:False})
    )
    funded_bys_ = funded_bys_.rename(columns={"OTHER":'OTHER FUND SOURCE'})

    # merge
    df_= (
        df.drop(columns = ['Title','Locations','Conditions','Enrollment','URL',
                            'Location_City_or_State','Location_Institution','Start Date',
                            'Completion Date','First Posted','Last Update Posted',
                            'Trial_Duration_Days','Trial_Duration_Months','Funded Bys']).
        set_index('NCT Number').
        merge(study_designs_, left_index=True, right_index=True).
        merge(mask, left_index=True, right_index=True).
        merge(interventions_type, left_index=True, right_index=True).
        merge(funded_bys_, left_index=True, right_index=True).
        replace({np.nan:"NO RECORD", "NAN":"NO RECORD", "N/A":"NO RECORD"})
    )   

    return df_

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
    basic_info_cols = ["Status", "Phases", "Study Type", "Study Results", "Location_Country", "Trial_Duration_Category",
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
    km = KModes(**best_para_dict, n_init = 3,verbose=0)

    return km

def plot_cluster(km=get_cluster(), df=choose_feature(), feature="Study Type"):
    """
    this function plot how categories distributed in each cluster for a specific feature
    Parameters
    ----------
    km
        a kmode cluster algo
    df : pandas.DataFrame
        data frame of features that used to cluster
    feature: str
        which feature to display, this feature must be in df
    Returns
    ----------
    plot:
        the plot demonstrate how category distributed in each cluster for a specific feature
    """
    fitClusters = km.fit_predict(df)
    clustersDf = pd.DataFrame(fitClusters)
    clustersDf.columns = ['Cluster Predicted']
    df_with_cluster = df.reset_index().merge(clustersDf, left_index=True, right_index=True).set_index("NCT Number")
    df_count_cluster = df_with_cluster.assign(count=1).groupby(['Cluster Predicted',feature]).agg({"count":'count'}).reset_index()

    plot = px.bar(df_count_cluster, x="Cluster Predicted", y="count",color=feature, barmode='group') 

    return plot

# test 
if __name__=="__main__":
    plot_cluster(feature="Trial_Duration_Category").show()
