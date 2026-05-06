from datetime import datetime, timedelta
import requests
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import streamlit as st
import kagglehub
import os
from bs4 import BeautifulSoup
import re
import requests


@st.cache_data
def load_earthquake_data():
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = datetime.today() - timedelta(days=365)
    base_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    min_magnitude = 3

    while True:
        url = f"{base_url}?format=geojson&starttime={start_date.strftime('%Y-%m-%d')}&endtime={end_date}&minmagnitude={min_magnitude}&limit=2000"
        response = requests.get(url)

        if not response.ok:
            # Move start date forward to reduce results and retry
            start_date += timedelta(days=30)
            continue

        try:
            data = response.json()
        except Exception:
            start_date += timedelta(days=30)
            continue

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
def clean_volcanos_of_earth():

    path = kagglehub.dataset_download("deepcontractor/the-volcanoes-of-earth")
    file_path = os.path.join(path, "The_Volcanoes_Of_Earth.csv")
    volcanoes_of_earth = pd.read_csv(file_path)
    
    volcanoes_of_earth.columns = [column.lower() for column in volcanoes_of_earth.columns]
    volcanoes_of_earth = volcanoes_of_earth[['volcano_name', 'volcano_image', 'volcano_type', 'epoch_period', 'summit_and_elevatiuon']]

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


    volcanoes_of_earth['volcano_type'].value_counts()

    # Renaming the column to "elevation"
    volcanoes_of_earth.rename(columns={'summit_and_elevatiuon':'elevation'}, inplace=True)
    # Replacing manually the value for Aak volcano
    volcanoes_of_earth.loc[1343, 'elevation'] = 2319
    volcanoes_of_earth.loc[1343, 'volcano_image'] = 'https://volcano.si.edu/gallery/photos/GVP-12487.jpg'
    
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

    
    return volcanoes_of_earth


@st.cache_data
def clean_eruptions():
    path = kagglehub.dataset_download("jessemostipak/volcano-eruptions")

    eruptions_path = os.path.join(path, "eruptions.csv")
    eruptions = pd.read_csv(eruptions_path)

    eruptions = eruptions[['volcano_name', 'vei', 'start_year', 'end_year', 'latitude', 'longitude']]
    eruptions.dropna(subset=['start_year'], inplace=True)
    eruptions['vei'] = eruptions['vei'].fillna(-1)

    eruptions["start_year"] = pd.to_numeric(eruptions['start_year'], downcast='integer', errors='coerce')
    eruptions.rename(columns={"start_year": "year"}, errors="raise", inplace=True)

    eruptions[(eruptions["latitude"] == -21.338) & (eruptions["longitude"] == -175.650)]

    
    # Manually adding volanic names based on latitude and logitude to unnamed ones
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
    
    return eruptions


@st.cache_data
def load_eruption_data():
    
    eruptions = clean_eruptions()
    volcanoes_of_earth = clean_volcanos_of_earth()
    eruptions_and_types = pd.merge(eruptions, volcanoes_of_earth, on='volcano_name', how='inner')

    return eruptions_and_types


@st.cache_data
def load_first_and_last_eruption_year(eruptions_and_types):
    eruptions_and_types['first_eruption_year'] = eruptions_and_types.groupby('volcano_name')['year'].transform('min')
    eruptions_and_types['last_eruption_year'] = eruptions_and_types.groupby('volcano_name')['year'].transform('max')

    return eruptions_and_types


@st.cache_data
def scrap_volcanic_weekly_report():

    url = "https://volcano.si.edu/reports_weekly.cfm?vtab=feeds"
    response = requests.get(url)

    soup = BeautifulSoup(response.content)
    table = soup.find('table')

    volcano_data = []
    headers = [th.get_text(strip=True) for th in table.find_all('th')][1:]

    for row in table.find_all('tr')[2:]:  # Skip header row
        cols = row.find_all(['td', 'th'])

        if len(cols) < len(headers):
            print("Skipping row: not enough columns")
            continue

        try:
            volcano_link = row.find('a', href=re.compile(r'#vn_'))
            
            if not volcano_link:
                print("No volcano link found in this row")
                continue
            
            volcano_id = volcano_link['href'].split('#vn_')[1]
            volcano_name = volcano_link.get_text(strip=True)
            start_date = cols[3].get_text(strip=True)
            
            report_status = row.find("a", attrs={"data-tooltip": True})
            report_text = report_status.get_text(strip=True) if report_status else None

            row_data = {
                'volcano_id': volcano_id,
                'volcano_name': volcano_name,
                'start_date': start_date,
                'report_status': report_text
            }
            
            volcano_data.append(row_data)
        
        except Exception as e:
            print(f"Error processing row: {e}")

    volcanic_weekly_report = pd.DataFrame(volcano_data)

    return volcanic_weekly_report


@st.cache_data
def load_weekly_report():
    weekly_report = scrap_volcanic_weekly_report()
    volcanoes_of_earth = clean_volcanos_of_earth()
    eruptions = clean_eruptions()

    weekly_report = pd.merge(weekly_report, volcanoes_of_earth, on='volcano_name', how='inner')
    weekly_report = pd.merge(weekly_report, eruptions[['volcano_name', "latitude", "longitude"]], on='volcano_name', how='inner').drop_duplicates().reset_index(drop=True)

    return weekly_report


@st.cache_data
def scrap_yearly_report():
    url = "https://volcano.si.edu/faq/index.cfm?question=eruptionsbyyear&checkyear=2025"
    response = requests.get(url)

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the table - you might need to adjust the selector based on the actual page structure
    table = soup.find('table')

    # Extract table data
    data = []

    # Get table headers
    headers = []
    for th in table.find_all('th'):
        headers.append(th.text.strip())

    # Get table rows
    for row in table.find_all('tr')[1:]:  # Skip the header row
        row_data = []
        for td in row.find_all('td'):
            row_data.append(td.text.strip())
        
        if row_data:  # Skip empty rows
            data.append(row_data)

    # Create a DataFrame
    yearly_report = pd.DataFrame(data, columns=headers)
    yearly_report.columns = [column.lower() for column in yearly_report.columns]
    return yearly_report


@st.cache_data
def clean_yearly_report():
    date_column = 'eruption stop date'
    
    df = scrap_yearly_report()
    # Create the status column with default 'Over'
    df['status'] = 'Over'
    
    # Update status based on the continuing text
    mask = df[date_column].str.contains('\(continuing\)', regex=True, na=False)
    df.loc[mask, 'status'] = 'Continuing'
    
    # Clean up the date strings
    df[date_column] = df[date_column].str.replace(r'\s*\(continuing\)\s*', '', regex=True)
    
    # Count and print how many ongoing eruptions were found
    ongoing_count = df['status'].value_counts().get('On going', 0)
    print(f"Found {ongoing_count} ongoing eruptions")

    df = df[['volcano', 'country', 'eruption start date', 'eruption stop date', 'status', 'max vei']]
    df.rename(columns={'volcano':'volcano_name'}, inplace=True)
    
    return df


@st.cache_data
def load_yearly_report():
    yearly_report = clean_yearly_report()
    volcanoes_of_earth = clean_volcanos_of_earth()
    eruptions = clean_eruptions()

    yearly_report = pd.merge(yearly_report, volcanoes_of_earth, on='volcano_name', how='inner')
    yearly_report = pd.merge(yearly_report, eruptions[['volcano_name', "latitude", "longitude"]], on='volcano_name', how='inner').drop_duplicates().reset_index(drop=True)

    return yearly_report
    