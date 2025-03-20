from datetime import datetime, timedelta
import requests
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import streamlit as st
import kagglehub
import os


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
    earthquakes_df['datetime'] = pd.to_datetime(earthquakes_df['time'], unit='ms').dt.strftime("%d.%m.%Y at %H:%M:%S")
    # Drop unnecessary columns
    earthquakes_df.drop("time", axis = 1, inplace=True)

    return earthquakes_df, start_date


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


@st.cache_data
def load_eruption_data():
    # Loading datasets
    eruptions_path = kagglehub.dataset_download("jessemostipak/volcano-eruptions")
    volcanoes_path = kagglehub.dataset_download("deepcontractor/the-volcanoes-of-earth")
    
    eruptions_file = os.path.join(eruptions_path, "eruptions.csv")
    volcanoes_file = os.path.join(volcanoes_path, "The_Volcanoes_Of_Earth.csv")

    eruptions = pd.read_csv(eruptions_file)
    volcanoes_of_earth = pd.read_csv(volcanoes_file)

    # Cleaning eruptions dataset
    eruptions = eruptions[['volcano_name', 'vei', 'start_year',	'latitude', 'longitude']]
    eruptions.dropna(subset=['start_year'], inplace=True)
    eruptions['vei'] = eruptions['vei'].fillna(-1)
    eruptions["start_year"] = pd.to_numeric(eruptions['start_year'], downcast='integer', errors='coerce')
    eruptions.rename(columns={"start_year": "year"}, errors="raise", inplace=True)

    # Cleaning volcano names
    volcano_names = {
    (-20.852, -175.550): 'Hunga Tonga-Hunga Ha\'apai',
    (-18.325, -174.365): 'Late Island',
    (46.470, 151.280): 'Chirinkotan',
    (45.022, 147.019): 'Ekarma',
    (-21.338, -175.650): 'Kao',
    (21.830, 121.180): 'Green Island',
    (20.330, 121.750): 'Babuyan Claro',
    (24.132, 121.926): 'Qixing Mountain'
    }

    # Update the volcano names
    eruptions['volcano_name'] = eruptions.apply(
        lambda row: volcano_names.get((row['latitude'], row['longitude']), row['volcano_name']),
        axis=1
    )

    # Cleaning volcanos on earth
    volcanoes_of_earth.columns = [column.lower() for column in volcanoes_of_earth.columns]
    volcanoes_of_earth = volcanoes_of_earth[['volcano_name', 'volcano_type', 'epoch_period', 'summit_and_elevatiuon']]

    volcanoes_of_earth['volcano_type'] = volcanoes_of_earth['volcano_type'].replace({
        "Stratovolcano":"Stratovolcano(es)",
        "Stratovolcano?": "Stratovolcano(es)",
        "Pyroclastic cone": "Pyroclastic cone(s)",
        "Shield": "Shield(s)",
        "Shield?": "Shield(s)",
        "Lava dome": "Lava dome(s)",
        "Caldera": "Caldera(s)",
        "Caldera(?)": "Caldera(s)",
        "Tuff cone": "Tuff cone(s)",
        "Complex": "Complex(es)",
        "Lava cone": "Lava cone(s)",
        "Lava cone(es)": "Lava cone(s)",
        "Cone": "Cone(s)",
        "Explosion crater": "Explosion crater(s)",
        "Explosion crater(?)": "Explosion crater(s)",
        "Lava dome(s) ?": "Lava dome(s)",
        "Fissure vent(s) ?": "Fissure vent(s)"
    })

    volcanoes_of_earth['epoch_period'] = volcanoes_of_earth['epoch_period'].replace({
        "holocene":"Holoceno",
        "pleistocene": "Pleistocene"
    })

    # Renaming the column to "elevation"
    volcanoes_of_earth.rename(columns={'summit_and_elevatiuon':'elevation'}, inplace=True)
    # Replacing manually the value for Aak volcano
    volcanoes_of_earth.loc[1343, 'elevation'] = 2319
    
    # Process the elevation column
    for index, value in volcanoes_of_earth['elevation'].items():
        if isinstance(value, str) and "Unknown," in value:
            volcanoes_of_earth.at[index, 'elevation'] = -99999
        elif isinstance(value, str): 
            volcanoes_of_earth.at[index, 'elevation'] = int(value.split()[0])
        elif isinstance(value, (int, float)):
            volcanoes_of_earth.at[index, 'elevation'] = int(value)
        else:
            volcanoes_of_earth.at[index, 'elevation'] = -99999

    eruptions_and_types = pd.merge(eruptions, volcanoes_of_earth, on='volcano_name', how='left')

    return eruptions_and_types


@st.cache_data
def load_first_and_last_eruption_year(eruptions_and_types):
    eruptions_and_types['first_eruption_year'] = eruptions_and_types.groupby('volcano_name')['year'].transform('min')
    eruptions_and_types['last_eruption_year'] = eruptions_and_types.groupby('volcano_name')['year'].transform('max')

    return eruptions_and_types