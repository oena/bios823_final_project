# BIOS823 Final Project:  Team Polar Bear

## Members

Oana Enache (Biostatistics Department, Duke University School of Medicine) 

Yi Mi (Statistical Science Department, Duke University)

Yue Han (Economics Department, Duke University)

## Project information

### Data set

The data set we will be using is the information on [ongoing clinical trials related to COVID-19 from clinicaltrials.gov](https://clinicaltrials.gov/ct2/results?cond=COVID-19). In raw form, this data is in tabular format but has very messy data fields. 

### Project objective and benefits

#### Data product and user benefit

The final product will be a dashboard displaying several fields of the information available on ongoing trials. This will benefit the consumer because it will make it much more simple and intuitive to find and understand basic information about what trials are ongoing (eg. where are they happening? what drugs are being considered? etc). Although there is considerable information currently available on clinicaltrials.gov, the information for 3,411 studies is currently displayed as a very dense text table that makes it hard to understand the bigger picture of what research/studies are ongoing for this issue. For example, to simpy see what countries have ongoing trials using the currently available data a user would have to click through the entire table (which would correspond to 340 page clicks for the default display of 10 studies/page) and keep track of locations represented themselves in some manner. 

#### Data science plan 

1. Exploratory data analysis to get a sense for what questions can be addressed by the dashboard, and what data is available. 

2. Extract relevant fields from clinical trials site and tidy data. 

3. Load cleaned data into a SQL server. 

4. Create relevant visualizations using `plotly`. 

5. Create a dashboard containing visualizations using `dash`. 

6. Deploy dashboard on AWS. 

#### Roles, responsibilities, and milestones

By October 9th: 
- Extract relevant fields from trial site, and tidy data (Oana) 

By October 16th:
- Set up SQL server and load cleaned data (Yi) 
- Create relevant visualizatiions with plotly (Yue) 

By October 30th:
- Set up dashboard containing visualizations with Dash (Oana) 
- Migrate SQL server to AWS (Yi) 
- Set up dashboard on AWS (Oana, Yue) 


