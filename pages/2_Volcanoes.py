import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

from utils.utils import load_eruption_data, load_top_10_eruptions_count

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
eruptions_and_types = get_eruptions_and_types()


# Cache Data Loading
# @st.cache_data
# def get_top_10_eruptions_count():
#     return load_top_10_eruptions_count(eruptions_and_types)


# # Load Data (cached)
# top_10_eruptions_count = get_top_10_eruptions_count()

top_10_eruptions_count = load_top_10_eruptions_count(eruptions_and_types)



st.title("🌋 Volcanoes")

# Count the number of eruptions per volcano
eruption_counts = eruptions_and_types.groupby('volcano_name').size().reset_index(name='eruption_count')

# Group by volcano_name and get the latest eruption details
latest_eruptions = eruptions_and_types.sort_values('year', ascending=False).drop_duplicates('volcano_name')

# Merge the counts back into the latest_eruptions DataFrame
latest_eruptions = latest_eruptions.merge(eruption_counts, on='volcano_name')

# Create a base map centered on the first volcano
volcano_map = folium.Map(location=[20, 0], zoom_start=2, min_zoom=2, tiles="Esri.WorldImagery")

# Add markers for each volcano
for _, row in latest_eruptions.iterrows():
    popup_text = f"""
    <b>Volcano:</b> {row['volcano_name']}<br>
    <b>Latest Eruption:</b> {row['year']}<br>
    <b>VEI:</b> {row['vei']}<br>
    <b>Type:</b> {row['volcano_type']}<br>
    <b>Epoch:</b> {row['epoch_period']}
    """
    popup = folium.Popup(popup_text, max_width=300)

    marker_size = row['eruption_count'] * 0.1

    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=marker_size,
        color="yellow",
        fill=True,
        fill_color="yellow",
        fill_opacity=0.8,
        popup=popup,
        tooltip=f"{row['volcano_name']} ({row['eruption_count']} eruptions)",
    ).add_to(volcano_map)

# Display the map in Streamlit
st.subheader("Volcano Locations and their frequency")
st_folium(volcano_map, width="100%", height=500)

st.subheader("Top 10 highest eruption count")
st.dataframe(top_10_eruptions_count
             .rename(columns = {
                 "volcano_name": "Volcano", 
                 "volcano_type": "Volcano Type", 
                 "elevation": "Elevation (m)", 
                 "first_eruption_year": "First eruption year", 
                 "last_eruption_year":"Last eruption year", 
                 "eruption_count": "Eruption count"})
             .style.background_gradient(cmap='YlOrRd', subset=['Eruption count']))
             