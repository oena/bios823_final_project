import pandas as pd 
import numpy as np
import sqlite3
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

columns_of_interest = ['NCT Number', 
                       'Title', 
                       'Locations',
                       'Status', 
                       'Study Results',
                       'Conditions', 
                       'Interventions', 
                       'Outcome Measures', 
                       'Sponsor/Collaborators', 
                       'Gender', 
                       'Age', 
                       'Phases', 
                       'Enrollment',
                       'Funded Bys', 
                       'Study Type', 
                       'Study Designs',
                       'Start Date',
                       'Completion Date',
                       'First Posted',
                       'Last Update Posted',
                       'URL']

date_columns = ['Start Date',                       
                'Completion Date',
                'First Posted',
                'Last Update Posted' ]

def pre_processing(filename):
    """A function used to get the data and pre-process the data to the big data frame.

    Parameters
    ----------
    str:
        the filename of dataset.
    
    Returns
    -------
    dataframe:
        return the dataframe of the covid trial data.
    
    Examples
    --------
    >>> df = pre_processing()
    """
    
    covid_trials_df = pd.read_csv(filename, sep="\t")

    # select the columns
    covid_trials_df = covid_trials_df[columns_of_interest]

    # Only keep month and year
    for d in date_columns:
        covid_trials_df[d] = [(str(i).split(" ")[0] + " " + str(i).split(" ")[-1]) for i in list(covid_trials_df[d])]
    
    # Add a countries column
    covid_trials_df.loc[:,"Location_Country"] = [str(i).split(",")[-1].strip() for i in list(covid_trials_df["Locations"].copy())]
    # fix Incorrectly named country columns 
    covid_trials_df["Location_Country"].loc[covid_trials_df["Location_Country"] == "Islamic Republic of"] = "Iran"
    covid_trials_df["Location_Country"].loc[covid_trials_df["Location_Country"] == "The Democratic Republic of the"] = "Congo"


    # Add a countries column
    covid_trials_df.loc[:,"Location_City_or_State"] = [str(i).split(",")[-2].strip() 
                                                    if len(str(i).split(",")) > 1 
                                                    else str(i)
                                                    for i in list(covid_trials_df["Locations"].copy())]


    covid_trials_df.loc[:,"Location_Institution"] = [str(i).split(",")[0].strip()  
                                                    for i in list(covid_trials_df["Locations"].copy())]

    covid_trials_df = covid_trials_df.applymap(lambda s:s.upper() if type(s) == str else s)
    covid_trials_df = covid_trials_df.replace("nan", np.nan)
    covid_trials_df = covid_trials_df.replace("NaN", np.nan)

    return covid_trials_df

def split_df(covid_trials_df):
    """A function used to split the big covid trail dataframe into several small dataframes in order to follow 3NF.

    Parameters
    ----------
    dataframe:
        the big dataframe.
    
    Returns
    -------
    study_designs: 
        the study design dataframe, including 'NCT Number' and 'Study Designs' fields.
    interventions:
        the interventions dataframe, including 'NCT Number' and 'Interventions' fields.
    outcome_measures:
        the outcome measures dataframe, including 'NCT Number' and 'Outcome Measures' fields.
    sponsor_collaborators:
        the sponsor/collaborators dataframe, including 'NCT Number' and 'Sponsor/Collaborators' fields.
    funded_bys:
        the funded bys dataframe, including 'NCT Number' and 'Funded Bys' fields.
    study_type:
        the study type dataframe, including 'NCT Number' and 'Study Type' fields.
    trial_info:
        other info except the info from above dataframes.

    Examples
    --------
    >>> study_designs, interventions, outcome_measures, sponsor_collaborators, funded_bys, study_type, trial_info = split_df(df)
    """

    study_designs = covid_trials_df[['NCT Number', 'Study Designs']].drop_duplicates() # pk: NCT number
    interventions = covid_trials_df[['NCT Number', 'Interventions']].drop_duplicates() # pk: NCT number
    outcome_measures = covid_trials_df[['NCT Number', 'Outcome Measures']].drop_duplicates() # pk: index
    sponsor_collaborators = covid_trials_df[['NCT Number', 'Sponsor/Collaborators']].drop_duplicates() # pk: index
    funded_bys = covid_trials_df[['NCT Number', 'Funded Bys']].drop_duplicates() # pk: index
    study_type = covid_trials_df[['NCT Number', 'Study Type']].drop_duplicates() # pk: index

    trial_into_list = ['NCT Number', 'Title', 'Locations', 'Status', 'Study Results', 'Conditions',
                   'Gender', 'Age', 'Phases','Enrollment', 'URL', 'Location_Country', 'Location_City_or_State',
                   'Location_Institution', 'Start Date', 'Completion Date', 'First Posted','Last Update Posted',
                   'Funded Bys', 'Study Type']
    trial_info = covid_trials_df[trial_into_list].drop_duplicates()

    outcome_measures = outcome_measures.assign(**{'Outcome Measures':outcome_measures['Outcome Measures'].str.split('|')})
    outcome_measures = outcome_measures.explode('Outcome Measures')
    sponsor_collaborators = sponsor_collaborators.assign(**{'Sponsor/Collaborators':sponsor_collaborators['Sponsor/Collaborators'].str.split('|')})
    sponsor_collaborators = sponsor_collaborators.explode('Sponsor/Collaborators')
    funded_bys = funded_bys.assign(**{'Funded Bys':funded_bys['Funded Bys'].str.split('|')})
    funded_bys = funded_bys.explode('Funded Bys')
    study_type = study_type.assign(**{'Study Type':study_type['Study Type'].str.split('|')})
    study_type = study_type.explode('Study Type')

    outcome_measures.reset_index(drop=True, inplace=True)
    outcome_measures['index'] = outcome_measures.index
    sponsor_collaborators.reset_index(drop=True, inplace=True)
    sponsor_collaborators['index'] = sponsor_collaborators.index
    funded_bys.reset_index(drop=True, inplace=True)
    funded_bys['index'] = funded_bys.index
    study_type.reset_index(drop=True, inplace=True)
    study_type['index'] = study_type.index

    return study_designs, interventions, outcome_measures, sponsor_collaborators, funded_bys, study_type, trial_info


def process_study_design(study_designs):
    """A function used to process the study design dataframe, by expanding JSON data and transferring to short form.

    Parameters
    ----------
    dataframe:
        the study design dataframe.
    
    Returns
    -------
    dataframe: 
        the tansferred study design dataframe, including 'NCT Number', "ALLOCATION", "INTERVENTION MODEL", "MASKING",
        "PRIMARY PURPOSE", "OBSERVATIONAL MODEL", "TIME PERSPECTIVE" fields.

    Examples
    --------
    >>> study_designs_new = process_study_design(study_designs)
    """

    study_design_list = ["ALLOCATION", 
                     "INTERVENTION MODEL", 
                     "MASKING",
                     "PRIMARY PURPOSE",
                     "OBSERVATIONAL MODEL",
                     "TIME PERSPECTIVE"] 
    def parse_study_design(row):
        """A function used to parse the string into JSON data inside study design cells.

        Parameters
        ----------
        dataframe row:
            each row of study design dataframe.

        Returns
        -------
        dictionary: 
            the parsed study design string data.

        Examples
        --------
        >>> study_design_df = study_designs['Study Designs'].apply(parse_study_design)
        """
        
        dic = {}
        for i in range(len(study_design_list)):
            dic[study_design_list[i]] = 'nan'
        try:
            row = row.split("|")
            for item in row:
                item = item.split(":")
                key = item[0].strip()
                value = item[1].strip()
                if key in dic:
                    dic[key] = value
            return dic
        except:
            return dic
    study_design_df = study_designs['Study Designs'].apply(parse_study_design)
    study_designs.loc[:,study_design_list] = pd.json_normalize(study_design_df)
    study_designs.drop('Study Designs', axis=1, inplace=True) 
    study_designs = study_designs.replace("nan", np.nan)
    study_designs = study_designs.replace("N/A", np.nan)
    return study_designs


def process_intervention(interventions):
    """A function used to process the interventions dataframe, by expanding JSON data and transferring to short form.

    Parameters
    ----------
    dataframe:
        the interventions dataframe.
    
    Returns
    -------
    dataframe: 
        the tansferred interventions dataframe, including 'NCT Number', 'DRUG', 'PROCEDURE', 'OTHER', 'DEVICE', 
        'BIOLOGICAL', 'DIAGNOSTIC TEST', 'DIETARY SUPPLEMENT', 'GENETIC', 'COMBINATION PRODUCT', 'BEHAVIORAL', 
        'RADIATION'.

    Examples
    --------
    >>> interventions_new = process_intervention(interventions)
    """

    intervention_list = ['DRUG', 'PROCEDURE', 'OTHER', 'DEVICE', 'BIOLOGICAL', 'DIAGNOSTIC TEST',
                     'DIETARY SUPPLEMENT', 'GENETIC', 'COMBINATION PRODUCT', 'BEHAVIORAL', 'RADIATION'] 
    
    def parse_intervention(row):
        """A function used to parse the string into JSON data inside intervention cells.

        Parameters
        ----------
        dataframe row:
            each row of intervention dataframe.

        Returns
        -------
        dictionary: 
            the parsed intervention string data.

        Examples
        --------
        >>> intervention_df = interventions['Interventions'].apply(parse_intervention)
        """
        dic = {}
        for i in range(len(intervention_list)):
            dic[intervention_list[i]] = 'nan'
        try:
            row = row.split("|")
            for item in row:
                item = item.split(":")
                key = item[0].strip()
                value = item[1].strip()
                if key in dic:
                    dic[key] = value
            return dic
        except:
            return dic
        
    intervention_df = interventions['Interventions'].apply(parse_intervention)
    interventions.loc[:,intervention_list] = pd.json_normalize(intervention_df)
    interventions.drop('Interventions', axis=1, inplace=True) 
    interventions = interventions.replace("nan", np.nan)
    interventions = interventions.replace("N/A", np.nan)
    return interventions


def checkPK(df, pk):
    if np.any(df[pk].isnull()):
        print('NULL values.')
    elif df[pk].drop_duplicates().shape[0] != df.shape[0]:
        print('Duplication.')
    else:
        print('Valid PK.')

def clean_and_set_up_db(df_path):
    covid_trials_df = pre_processing(df_path)
    study_designs, interventions, outcome_measures, sponsor_collaborators, funded_bys, study_type, trial_info = split_df(covid_trials_df)
    study_designs_new = process_study_design(study_designs)
    interventions_new = process_intervention(interventions)

    conn = sqlite3.connect('covid_trials.db')
    study_designs.to_sql('study_designs', conn, if_exists='replace', index=False)
    interventions.to_sql('interventions', conn, if_exists='replace', index=False)
    trial_info.to_sql('trial_info', conn, if_exists='replace', index=False)
    outcome_measures.to_sql('outcome_measures', conn, if_exists='replace', index=False)
    sponsor_collaborators.to_sql('sponsor_collaborators', conn, if_exists='replace', index=False)
    funded_bys.to_sql('funded_bys', conn, if_exists='replace', index=False)
    study_type.to_sql('study_type', conn, if_exists='replace', index=False)


if __name__ == "__main__":
    # TODO: consider changing this to call method above
    covid_trials_df = pre_processing("SearchResults_new.tsv")
    study_designs, interventions, outcome_measures, sponsor_collaborators, funded_bys, study_type, trial_info = split_df(covid_trials_df)
    study_designs_new = process_study_design(study_designs)
    interventions_new = process_intervention(interventions)
    
    conn = sqlite3.connect('covid_trials.db')
    study_designs.to_sql('study_designs', conn, if_exists='replace', index=False)
    interventions.to_sql('interventions', conn, if_exists='replace', index=False)
    trial_info.to_sql('trial_info', conn, if_exists='replace', index=False)
    outcome_measures.to_sql('outcome_measures', conn, if_exists='replace', index=False)
    sponsor_collaborators.to_sql('sponsor_collaborators', conn, if_exists='replace', index=False)
    funded_bys.to_sql('funded_bys', conn, if_exists='replace', index=False)
    study_type.to_sql('study_type', conn, if_exists='replace', index=False)







