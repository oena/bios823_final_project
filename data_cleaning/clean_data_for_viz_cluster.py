from datetime import datetime
import json
import re
import sqlite3

import numpy as np 
import pandas as pd
import geopandas as gpd


# get data functions ###################################################################################################

def get_df():
    """
    this function load cleaned data and then transform it to df, which will be use to generate visualization
    """
    # Read in dataset
    conn = sqlite3.connect('covid_trials.db')
    df = pd.read_sql("select * from trial_info", con = conn)
    conn.close()

    # Preprocessing data
    ## age
    df['Age'] = df.Age.str.extract(r'[(](.*?)[)]')

    ## date
    date_columns = ['Start Date',
                    'Completion Date',
                    'First Posted',
                    'Last Update Posted']

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
    
    ## clean country name
    def rename_country(old_name):
        name_match = {
            'UNITED STATES': 'UNITED STATES OF AMERICA',
            'RUSSIAN FEDERATION': 'RUSSIA',
            'HONG KONG': 'HONG KONG S.A.R.',
            'CONGO': 'DEMOCRATIC REPUBLIC OF THE CONGO',
            'REPUBLIC OF': 'DEMOCRATIC REPUBLIC OF THE CONGO',
            'NORTH MACEDONIA': 'MACEDONIA',
            'CÔTE D\'IVOIRE': 'IVORY COAST',
            'FRENCH GUIANA': 'GUINEA',
            'GIBRALTAR': 'SPAIN',
            'MARTINIQUE': 'FRANCE'
        }
        for k, v in name_match.items():
            if old_name == k:
                return v
        if not old_name in set(name_match):
            return old_name

    df['Location_Country'] = df.Location_Country.apply(rename_country)

    ## clean study type variable
    df["Study Type"] = (
        df["Study Type"].
        replace({"TREATMENT IND/PROTOCOL":"EXPANDED ACCESS",
                "INTERMEDIATE-SIZE POPULATION":"EXPANDED ACCESS",})
        .replace(regex={r'EXPANDED ACCESS:.*':"EXPANDED ACCESS"})
    )

    return df

def get_data_for_map(df = get_df()):
    # load the data of geo information
    shapefile = '50m_cultural/ne_50m_admin_0_countries.shp'
    gdf = gpd.read_file(shapefile)[['ADMIN', 'geometry']]
    gdf = gdf[gdf.ADMIN != 'Antarctica']  # drop Antarctica since no people lives there
    gdf['ADMIN'] = gdf.ADMIN.apply(lambda x: x.upper())
    
    country_count_df = (
        df
        # add criteria here
        [['Location_Country']]
        [(df['Location_Country'] != 'NAN') & (df['Location_Country'] != 'REPUBLIC OF')].
        # the last criteria can be drop when we confirm what 'REPUBLIC OF' is
        assign(count=1).
        groupby(['Location_Country']).
        agg('sum').
        sort_values('count', ascending=False)
    )

    # equip data with geo info
    geo_country_count_df = (
        gdf.merge(country_count_df, left_on='ADMIN', right_on='Location_Country', how='left').
        sort_values('count', ascending=False)
    )
    
    return country_count_df, geo_country_count_df
    

def get_data_for_cluster():
    """
    this function return a merged df for cluster
    """
    # load in data
    conn = sqlite3.connect('covid_trials.db')
    study_designs=pd.read_sql("select * from study_designs", con = conn)
    interventions=pd.read_sql("select * from interventions", con = conn)
    funded_bys=pd.read_sql("select * from funded_bys", con = conn)
    conn.close()

    # trial info
    df = get_df()

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

# test #################################################################################################################

if __name__=="__main__":
    get_df().to_csv("cleaned_data_for_viz.tsv", sep="\t")
    get_data_for_map()[0].to_csv("cleaned_data_for_map.tsv", sep="\t")
    get_data_for_map()[1].to_csv("cleaned_data_for_map_with_geo.tsv", sep="\t")
    get_data_for_cluster().to_csv("cleaned_data_for_cluster.tsv", sep="\t")
    





