import pandas as pd

from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from tqdm import tqdm

## Get geographic information

# Read in data, subset to US only, and annotate with geographic coordinates
data_df = pd.read_csv("data/cleaned_covid_studies_092020.tsv", sep="\t")
us_data_df = data_df[data_df["Location_Country"] == "UNITED STATES"] #  Subset to US only

# Geocode US locations
geolocator = Nominatim(user_agent="my_cov_trial_dash")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
unique_locations = pd.DataFrame.from_dict({"Location_Institution": list(us_data_df["Location_Institution"].unique())})

tqdm.pandas()
unique_locations["Address"] = unique_locations["Location_Institution"].progress_apply(geocode)
unique_locations["lat"] = [i.latitude if i is not None else None for i in unique_locations["Address"]]
unique_locations["lon"] = [i.longitude if i is not None else None for i in unique_locations["Address"]]

us_data_df_with_geo = us_data_df.merge(unique_locations, how="left")

## Add intervention type & drug columns

# Intervention type
us_data_df_with_geo["Intervention Type"] = list([str(i).split(": ")[0] for i in list(us_data_df_with_geo["Interventions"])])

# Drug type
us_data_df_with_geo["Drug Type"] = [str(i).split(": ")[1] if str(i).split(": ")[0] in ["DRUG", "BIOLOGICAL"] else None for i in list(us_data_df_with_geo["Interventions"])]

us_data_df_with_geo.to_csv("cleaned_us_covid_studies_with_geo_092020.tsv", sep="\t")
