## Dashboard 

The deployed dashboard can be found [here](https://share.streamlit.io/oena/bios823_final_project/dashboard/app_main.py). 

This folder contains:
- All the files comprising different pages of the dashboard app (these begin with `app_`)
- Two auxiliary files: `viz.py` and `cluster.py`
- Dashboard assets in dashboard_data/ (these are input files for visualizations, etc). Since expensive computations can slow streamlit apps down, we tried to minimize these if possible. 

### Running the dashboard locally 

You can run this dashboard locally (after cloning the repository) by: 

1. Activating the python3_env conda environment (as described in the [conda environment directory](https://github.com/oena/bios823_final_project/tree/master/conda_environments)). 

2. From this directory, type `streamlit run app_main.py` in the terminal. 
