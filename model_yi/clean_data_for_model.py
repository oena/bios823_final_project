import pandas as pd 
import numpy as np
from datetime import datetime
import imblearn
from sklearn.model_selection import train_test_split
from sklearn.dummy import DummyClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier

### read data
covid_trials_df = pd.read_csv("data/SearchResults_new.tsv", sep="\t")

### column of interests
columns_of_interest = ['NCT Number', 'Title', 'Locations', 'Status', 'Study Results', 'Conditions', 
                       'Interventions', 'Outcome Measures', 'Sponsor/Collaborators', 'Gender', 'Age', 
                       'Phases', 'Enrollment', 'Funded Bys', 'Study Type', 'Study Designs', 'Start Date',
                       'Completion Date', 'First Posted', 'Last Update Posted', 'URL']

covid_trials_df = covid_trials_df[columns_of_interest]


### date
date_columns = ['Start Date',                       
                'Completion Date',
                'First Posted',
                'Last Update Posted' ]

for d in date_columns:
    # Only keep month and year
    covid_trials_df[d] = [(str(i).split(" ")[0] + " " + str(i).split(" ")[-1]) for i in list(covid_trials_df[d])]

### location
covid_trials_df.loc[:,"Location_Country"] = [str(i).split(",")[-1].strip() for i in list(covid_trials_df["Locations"].copy())]
covid_trials_df["Location_Country"].loc[covid_trials_df["Location_Country"] == "Islamic Republic of"] = "Iran"
covid_trials_df["Location_Country"].loc[covid_trials_df["Location_Country"] == "The Democratic Republic of the"] = "Congo"

covid_trials_df.loc[:,"Location_City_or_State"] = [str(i).split(",")[-2].strip() 
                                                   if len(str(i).split(",")) > 1 
                                                   else str(i)
                                                   for i in list(covid_trials_df["Locations"].copy())]
covid_trials_df.loc[:,"Location_Institution"] = [str(i).split(",")[0].strip()  
                                                   for i in list(covid_trials_df["Locations"].copy())]

### char
covid_trials_df = covid_trials_df.applymap(lambda s:s.upper() if type(s) == str else s)
covid_trials_df = covid_trials_df.replace("nan", np.nan)
covid_trials_df = covid_trials_df.replace("NaN", np.nan)

########################################################################################

### age
covid_trials_df['Age'] = covid_trials_df.Age.str.extract(r'[(](.*?)[)]')
covid_trials_df['Age'] = covid_trials_df['Age'].replace(np.nan, "OTHERS").astype("category")

### gender
covid_trials_df['Gender'] = covid_trials_df['Gender'].replace(np.nan, "All").astype("category")

### phases
covid_trials_df.replace({"EARLY PHASE 1": "PHASE 1", "PHASE 1|PHASE 2": "PHASE 2", "PHASE 2|PHASE 3":"PHASE 3"}, inplace=True)
covid_trials_df['Phases'] = covid_trials_df['Phases'].replace(np.nan, "NOT APPLICABLE").astype("category")

### Study Type
covid_trials_df.loc[covid_trials_df['Study Type'].str.contains('EXPANDED ACCESS'), 'Study Type'] = 'EXPANDED ACCESS'
covid_trials_df['Study Type'] = covid_trials_df['Study Type'].astype("category")

### results (has result or not)
covid_trials_df['Study Results'] = covid_trials_df['Study Results'].astype("category")

### funded bys
def parse_funded_bys(df):
    for col in ['INDUSTRY', 'NIH', 'OTHER', 'U.S. FED']:
        if col=='U.S. FED':
            newcol = 'Funded_US_FED'
        else:
            newcol = 'Funded'+'_'+col
        df.loc[df['Funded Bys'].str.contains(col), newcol] = 1
        df.loc[~df['Funded Bys'].str.contains(col), newcol] = 0
        df[newcol] = df[newcol].astype('category')
    return df
covid_trials_df = parse_funded_bys(covid_trials_df)

### locations
covid_trials_df['Locations'] = covid_trials_df['Locations'].replace(np.nan, "OTHERS").astype("category")

########################################################################################

### duration
from datetime import datetime

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

# https://blog.csdn.net/u010339879/article/details/79505570
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

covid_trials_df[date_columns] = covid_trials_df[date_columns].applymap(to_date)
covid_trials_df['Trial_Duration_Months'] = covid_trials_df.apply(
    get_interval_month, axis=1, args=('Start Date', 'Completion Date'))

########################################################################################

# imputation enrollment and in duration
from sklearn.impute import SimpleImputer
si = SimpleImputer(strategy='mean')
covid_trials_df[covid_trials_df.select_dtypes('number').columns] = si.fit_transform(covid_trials_df.select_dtypes('number'))

########################################################################################

### status
df = covid_trials_df[['NCT Number', 'Title', 'Conditions', 'Outcome Measures','Sponsor/Collaborators', 
                      'Status', 'Study Results','Funded_INDUSTRY','Funded_NIH','Funded_OTHER','Funded_US_FED',
                      'Gender', 'Age', 'Phases', 'Enrollment', 'Study Type',  'Locations', 'Trial_Duration_Months',
                      'Interventions','Study Designs']]
df.loc[df['Status'].isin(['RECRUITING','NOT YET RECRUITING','AVAILABLE']), 'Active'] = 1 #'ACTIVE, NOT RECRUITING',
df.loc[~df['Status'].isin(['RECRUITING','NOT YET RECRUITING','AVAILABLE']), 'Active'] = 0
df['Active'] = df['Active'].astype('category')

########################################################################################

# select cols
df_ml = df[['Active','Study Results','Funded_INDUSTRY','Funded_NIH','Funded_OTHER','Funded_US_FED',
           'Gender', 'Age', 'Phases', 'Enrollment', 'Study Type', 'Trial_Duration_Months']]
df_ml_orig = df_ml.copy()

df_x = df[['Study Results','Funded_INDUSTRY','Funded_NIH','Funded_OTHER','Funded_US_FED',
           'Gender', 'Age', 'Phases', 'Enrollment', 'Study Type', 'Trial_Duration_Months']]
df_y = df['Active']
df_x = pd.get_dummies(df_x)

# rename
import re
df_x = df_x.rename(columns = lambda x:re.sub('[^A-Za-z0-9_]+', '', x))

# split and deal with imbalance data
X_train, X_test, y_train, y_test = train_test_split(df_x, df_y, random_state=0, stratify=df_y)
import imblearn
X_train_resampled, y_train_resampled = imblearn.over_sampling.SMOTE().fit_resample(X_train, y_train)

X_train_resampled.to_csv('data/X_train.csv', index=False)
X_test.to_csv('data/X_test.csv', index=False)
y_train_resampled.to_csv('data/y_train.csv', index=False)
y_test.to_csv('data/y_test.csv', index=False)
df_ml_orig.to_csv('data/df_ml_orig.csv', index=False)

########################################################################################

import pandas_profiling as pp
df_ml_orig = pd.get_dummies(df_ml_orig)
profile = pp.ProfileReport(df_ml_orig)
profile.to_file("data_report.json")
profile.to_file("data_report.html")