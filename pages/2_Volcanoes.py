import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

from utils.utils import load_eruption_data

st.set_page_config(
    layout="wide",
    initial_sidebar_state="auto",
    page_title="🌋 Volcanoes",
    page_icon="🌋",
)

# Cache Data Loading
@st.cache_data
def get_eruptions_and_types():
    return load_eruption_data()

# Load Data (cached)
volcano_eruptions = get_eruptions_and_types()

st.title("🌋 Volcanoes")

# Group by volcano_name and get the latest eruption details
latest_eruptions = volcano_eruptions.sort_values('start_year', ascending=False).drop_duplicates('volcano_name')

# Create a base map centered on the first volcano
volcano_map = folium.Map(location=[20, 0], zoom_start=2, min_zoom=2, tiles="Esri.WorldImagery")

# Add markers for each volcano
for _, row in latest_eruptions.iterrows():
    popup_text = f"""
    <b>Volcano:</b> {row['volcano_name']}<br>
    <b>Latest Eruption:</b> {row['start_year']}<br>
    <b>VEI:</b> {row['vei']}<br>
    <b>Type:</b> {row['volcano_type']}<br>
    <b>Epoch:</b> {row['epoch_period']}
    """
    popup = folium.Popup(popup_text, max_width=300)

    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=2,
        color="yellow",
        fill=True,
        fill_color="yellow",
        fill_opacity=0.8,
        popup=popup,
        tooltip=row['volcano_name']
    ).add_to(volcano_map)

# Display the map in Streamlit
st.title("Volcano Locations")
st_folium(volcano_map, width="100%", height=500)

st.dataframe(volcano_eruptions)