import streamlit as st
import pandas as pd
import altair as alt
import folium
from streamlit_folium import st_folium
import branca.colormap as cm


from utils.utils import load_earthquake_data, load_plate_boundaries, get_tectonic_plate_data, load_weekly_report

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

@st.cache_data
def get_weekly_report():
    return load_weekly_report()


# Load Data (cached)
earthquakes_df, start_date = get_earthquake_data()
plate_boundaries = get_plate_boundaries_data()
earthquakes_with_plates = get_tectonic_plate_data(earthquakes_df)[:10]
volcanic_weekly_report = get_weekly_report()


## Header
st.title("Earthquakes & Volcanoes")
st.subheader("Real-Time Monitoring + Historical Insights 🌋🌍💥")


######### MAP

# Initialize Map (existing code)
m = folium.Map(location=[20, 10], zoom_start=2, min_zoom=2, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}", attr="Esri Topo")

# Add tectonic plates (existing code)
if not plate_boundaries.empty:
    folium.GeoJson(
        plate_boundaries,
        name="Tectonic Plates",
        style_function=lambda feature: {
            "color": "lightblue",
            "weight": 1,
            "opacity": 0.5,
        },
    ).add_to(m)

# --------------------------
# EARTHQUAKE MARKERS (Circles)
# --------------------------
if not earthquakes_with_plates.empty:
    # Earthquake colormap (red-yellow for magnitude)
    eq_colormap = cm.linear.YlOrRd_09.scale(
        earthquakes_with_plates['mag'].min(), 
        earthquakes_with_plates['mag'].max()
    )
    
    for _, row in earthquakes_with_plates.iterrows():
        popup_text = f"""
        <b>Earthquake:</b> {row['place']}<br>
        <b>Plate:</b> {row['tectonic_plate']}<br>
        <b>Magnitude (Mw):</b> {row['mag']}<br>
        <b>Depth:</b> {row['depth']} km<br>
        <i>Source: USGS</i>
        """
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=5 + row['mag'],  # Larger circles for bigger quakes
            color=eq_colormap(row['mag']),
            fill=True,
            weight=1,
            fill_opacity=0.7,
            popup=folium.Popup(popup_text, max_width=250),
            tooltip=f"Earthquake: M{row['mag']} at {row['place']}"
        ).add_to(m)

# --------------------------
# VOLCANO MARKERS (Triangle Icons)
# --------------------------
if not volcanic_weekly_report.empty:
    for _, row in volcanic_weekly_report.iterrows():
        popup_text = f"""
        <b>Volcano:</b> {row['volcano_name']}<br>
        <b>Status:</b> {row['report_status']}<br>
        <i>Source: Smithsonian GVP</i>
        """
        folium.RegularPolygonMarker(
            location=[row['latitude'], row['longitude']],
            number_of_sides=3,  
            radius=8, 
            rotation=-90,  
            fill_color='#d62728',  # Red color
            color='#7f0000',  # Darker border
            weight=1,
            fill_opacity=0.9,
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"Volcano: {row['volcano_name']} ({row['elevation']})"
        ).add_to(m)

# --------------------------
# FINAL TOUCHES
# --------------------------
# Add legends
eq_colormap.caption = "Earthquake Magnitude (Mw)"
m.add_child(eq_colormap)

# Add a mini-legend for volcanoes
legend_html = """
<div style="
    position: fixed; 
    bottom: 50px; 
    left: 50px; 
    width: 150px; 
    height: 80px; 
    border:2px solid grey; 
    z-index:9999; 
    font-size:14px;
    background: white;
    padding: 5px;
    ">
    <b>🌋 Legend</b><br>
    <i class="fa fa-circle" style="color: #ff7800"></i> Earthquake<br>
    <i class="fa fa-triangle" style="color: darkred"></i> Volcano
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# Add layer control
folium.LayerControl(collapsed=False).add_to(m)

# Display
st_folium(m, width='100%', height=600)

######### MOST RECENT SEISMIC ACTIVITY
# Get the most recent earthquake
most_recent_place = earthquakes_with_plates.iloc[0]["place"]
most_recent_datetime = earthquakes_with_plates.iloc[0]["datetime"]
most_recent_mag = earthquakes_with_plates.iloc[0]["mag"]
most_recent_depth = earthquakes_with_plates.iloc[0]["depth"]
most_recent_plate = earthquakes_with_plates.iloc[0]["tectonic_plate"]

st.markdown(f"Most recent seismic activity registered was on **{most_recent_datetime}**")
st.subheader(f"{most_recent_place}")

# Create a multi-column layout
col1, col2 = st.columns([1, 2])

with col1:
    st.metric(label="Magnitude", value=f"{most_recent_mag} Mw", border=True)
    st.metric(label="Depth", value=f"{most_recent_depth} Km", border=True)
    st.metric(label="Tectonic Plate", value=f"{most_recent_plate}", border=True)

with col2:
    st.map(pd.DataFrame({
            "lat": [earthquakes_with_plates.iloc[0]['latitude']],
            "lon": [earthquakes_with_plates.iloc[0]['longitude']]
        }), zoom=5, height=350)

st.divider()

######### MOST RECENT VOLCANIC ACTIVITY
st.dataframe(volcanic_weekly_report)