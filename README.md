# BIOS823 Final Project: Exploring COVID-19 related clinical trials in the U.S. and Beyond 

You can explore the deployed version of this app [here](https://share.streamlit.io/oena/bios823_final_project/dashboard/app_main.py). 

## Members (Team Polar Bear)

Oana Enache (Biostatistics Department, Duke University School of Medicine) 

Yi Mi (Statistical Science Department, Duke University)

Yue Han (Economics Department, Duke University)

## Project information

### Project objective and audience

Our intended audience for this project is people in the United States who might want to learn more about COVID-19-related clinical trials that are happening in general and/or to find information on trials in relevant U.S. locations to them. 

Consequently, our objective with this project was to:

1. Enable users to explore the clinical trials relevant to COVID-19 that are happening and that have happened (through both interactive visualizations and machine learning models using trial features).

2. Enable users to find trial information by specific location in the United States. 

### Data set

The data set we will be using is the information on [ongoing clinical trials related to COVID-19 from clinicaltrials.gov](https://clinicaltrials.gov/ct2/results?cond=COVID-19). In raw form, this data is in tabular format but has very messy data fields and many columns. 

#### Data product and user benefit

The final product will be a dashboard displaying several fields of the information available on ongoing trials. This will benefit the consumer because it will make it much more simple and intuitive to find and understand basic information about what trials are ongoing (eg. where are they happening? what drugs are being considered? etc). Although there is considerable information currently available on clinicaltrials.gov, the information for 3,411 studies is currently displayed as a very dense text table that makes it hard to understand the bigger picture of what research/studies are ongoing for this issue. For example, to simpy see what countries have ongoing trials using the currently available data a user would have to click through the entire table (which would correspond to 340 page clicks for the default display of 10 studies/page) and keep track of locations represented themselves in some manner. 

#### Data science plan 

1. Exploratory data analysis to get a sense for what questions can be addressed by the dashboard, and what data is available. 

2. Extract relevant fields from clinical trials site and tidy data. 

3. Create relevant visualizations using `plotly`. 

5. Create a dashboard containing visualizations using `streamlit`. 

6. Deploy dashboard on streamlit's sharing platform. 

#### Roles, responsibilities, and milestones

By October 9th: 
- Extract relevant fields from trial site, and tidy data (Oana) 
- Exploratory analyses (All) 

By November 5th:
- Set up SQL server and load cleaned data (Yi) 
- Create relevant visualizatiions with plotly (Yue) 

By November 20th:
- Set up dashboard with steramlit (Oana, Yue, Yi) 
- Work on models & visualizations thereof (Yue, Yi) 
- Explore ways to deploy streamlit dashboards & deploy dashboard (Oana) 
- Clean up repo (All) 

## Repository structure

- **conda_environments/**: YAML files to recreate consistent environments we used in various stages of the project. 
- **dashboard/**: Dashboard files and assets 
  - dashboard/
- **data_cleaning/**: Scripts used to clean and process data used 
- **exploratory_analyses/**: Notebooks containing exploratory analyses performed
- **models/**: Machine learning models incorporated into dashboard 
  - models/clustering_trial_features/: Notebooks relevant to clustering trials by similarity of features. 
  - models/predicting_active_status_of_trials/: Assets relevant to the supervised learning exercise of predicting trial activity status from trial features
- **visualization/**: Notebooks of exploratory plotly visualizations before putting together the dashboard
