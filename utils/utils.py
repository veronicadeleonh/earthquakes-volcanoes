from datetime import datetime, timedelta
import requests
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import streamlit as st


@st.cache_data
def load_earthquake_data():
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = datetime.today() - timedelta(days=365)
    base_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    min_magnitude = 3

    while True:
        url = f"{base_url}?format=geojson&starttime={start_date.strftime('%Y-%m-%d')}&endtime={end_date}&minmagnitude={min_magnitude}"
        response = requests.get(url)
        data = response.json()
        
        if 'features' not in data:
            raise ValueError("No 'features' key in the API response. Check the API URL or parameters.")
        
        if len(data['features']) <= 2000:
            break  # Exit the loop if the data is within the limit
        
        # Move start date forward to reduce results
        start_date += timedelta(days=30)

    features = data['features']
    earthquakes = []

    for earthquake in features:
        properties = earthquake['properties']
        geometry = earthquake['geometry']

        earthquake_data = {
            'place': properties['place'],
            'mag': properties['mag'],
            'time': properties['time'],
            'tsunami': properties['tsunami'],
            'sig': properties['sig'],
            'latitude': geometry['coordinates'][1],
            'longitude': geometry['coordinates'][0],
            'depth': geometry['coordinates'][2],
        }

        earthquakes.append(earthquake_data)
    
    earthquakes_df = pd.DataFrame(earthquakes)

    # Convert timestamp to datetime
    earthquakes_df['datetime'] = pd.to_datetime(earthquakes_df['time'], unit='ms').dt.strftime("%B %d, %Y %H:%M")
    # Drop unnecessary columns
    earthquakes_df.drop("time", axis = 1, inplace=True)

    return earthquakes_df


@st.cache_data
def load_plate_boundaries():
    plate_boundaries = gpd.read_file("data/PB2002_boundaries.json")
    return plate_boundaries

minor_to_major_plate = {
    "Juan de Fuca": "Pacific",
    "Okhotsk": "Eurasia",
    "Burma": "Eurasia",
    "Sunda": "Eurasia",
    "Yangtze": "Eurasia",
    "Amur": "Eurasia",
    "Aegean Sea": "Eurasia",
    "Caribbean": "North America",
    "Sandwich": "South America",
    "Nazca": "South America",
    "Cocos": "North America",
    "Panama": "North America",
    "Philippine Sea": "Pacific",
    "Tonga": "Pacific",
    "New Hebrides": "Pacific",
    "South Bismarck": "Pacific",
    "North Bismarck": "Pacific",
    "Mariana": "Pacific",
    "Kermadec": "Pacific",
    "Altiplano": "South America",
    "Maoke": "Australia",
    "Woodlark": "Australia",
    "Banda Sea": "Australia",
    "Okinawa": "Eurasia",
    "Futuna": "Pacific",
    "North Andes": "South America",
    "Arabia": "Eurasia",
    "Shetland": "Antarctica",
    "Manus": "Pacific",
    "Timor": "Australia",
    "Molucca Sea": "Pacific",
    "Balmoral Reef": "Australia",
    "Somalia": "Africa",
    "India": "Eurasia",
    "Birds Head": "Australia",
    "Easter": "Pacific",
    "Niuafo'ou": "Pacific",
    "Antarctica": "Antarctica",
}

@st.cache_data
def get_tectonic_plate_data(earthquakes_df):
    
    plates = gpd.read_file("data/PB2002_plates.json")

   # Convert latitude/longitude into geometry
    geometry = [Point(lon, lat) for lon, lat in zip(earthquakes_df['longitude'], earthquakes_df['latitude'])]
    earthquakes_gdf = gpd.GeoDataFrame(earthquakes_df, geometry=geometry, crs="EPSG:4326")

    # Perform spatial join to assign tectonic plates
    earthquakes_with_plates = gpd.sjoin(earthquakes_gdf, plates, how="left", predicate="within")

    # Rename columns
    earthquakes_with_plates.rename(columns={"PlateName": "tectonic_plate"}, inplace=True)

    # Drop unnecesary columns
    earthquakes_with_plates.drop(["geometry", "index_right", "LAYER", "Code"], axis=1, inplace=True)

    # Assign major plate to each earthquake
    earthquakes_with_plates["tectonic_plate"] = earthquakes_with_plates["tectonic_plate"].replace(minor_to_major_plate)
    
    return earthquakes_with_plates