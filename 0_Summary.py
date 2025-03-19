import streamlit as st
import folium
from streamlit_folium import st_folium
import branca.colormap as cm
import altair as alt


from utils.utils import load_earthquake_data, load_plate_boundaries, get_tectonic_plate_data

# Page Config
st.set_page_config(
    layout="wide",
    initial_sidebar_state="auto",
    page_title="Seismic Data",
    page_icon="🌍"
)

# Cache Data Loading
@st.cache_data
def get_earthquake_data():
    return load_earthquake_data()

@st.cache_data
def get_plate_boundaries_data():
    return load_plate_boundaries()

# Load Data (cached)
earthquakes_df, start_date = get_earthquake_data()
plate_boundaries = get_plate_boundaries_data()
earthquakes_with_plates = get_tectonic_plate_data(earthquakes_df)


## Header
st.title("Earthquakes & Volcanic Eruptions Data 🌋🌍💥")


######### MOST RECENT SEISMIC ACTIVITY
# Get the most recent earthquake
most_recent_place = earthquakes_with_plates.iloc[0]["place"]
most_recent_datetime = earthquakes_with_plates.iloc[0]["datetime"]
most_recent_mag = earthquakes_with_plates.iloc[0]["mag"]
most_recent_depth = earthquakes_with_plates.iloc[0]["depth"]
most_recent_plate = earthquakes_with_plates.iloc[0]["tectonic_plate"]

st.text(f"Most recent seismic activity registered")
st.subheader(f"{most_recent_place}")

# Create a multi-column layout
col1, col2, col3, col4 = st.columns(4)

# Display the most recent earthquake details
with col1:
    st.metric(label="Date & Time", value=most_recent_datetime, border=True)

with col2:
    st.metric(label="Magnitude", value=f"{most_recent_mag} Mw", border=True)

with col3:
    st.metric(label="Depth", value=f"{most_recent_depth} Km", border=True)

with col4:
    st.metric(label="Tectonic Plate", value=f"{most_recent_plate}", border=True)