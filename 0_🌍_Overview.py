import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import branca.colormap as cm
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

from utils.utils import load_earthquake_data, load_plate_boundaries, get_tectonic_plate_data, load_weekly_report, load_yearly_report, get_image_base64

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

@st.cache_data
def get_yearly_report():
    return load_yearly_report()



# Load Data (cached)
earthquakes_df, start_date = get_earthquake_data()
plate_boundaries = get_plate_boundaries_data()
earthquakes_with_plates = get_tectonic_plate_data(earthquakes_df)[:10]
volcanic_weekly_report = get_weekly_report()
volcanic_yearly_report = get_yearly_report()


st.warning('Page under construction', icon="🚧")


## Header
st.title("🌋 Global Volcanic & Seismic Activity Monitor")
st.markdown("""
    This interactive dashboard bridges real-time monitoring with historical analysis of Earth's most powerful geological events. Track live seismic activity (via USGS API) and global volcanic eruptions (via GVP data), explore historical trends, and visualize patterns across tectonic boundaries. Scientists, researchers, and hazard preparedness teams can use these tools to:  
    - Monitor current seismic/volcanic activity with filtering capabilities
    - Analyze eruption magnitude (VEI) and frequency trends
    - Explore geological profiles of active volcanoes
    - Correlate events with tectonic plate boundaries  
    """)

st.divider()

######### MAP
st.subheader("Live Geological Activity: Last 10 Eruptions & Earthquakes 🌋🌍💥")
st.write("The map shows recent seismic activity and volcanic events alongside tectonic plate boundaries.")

# Create a two-column layout
col1, col2 = st.columns([3, 1])  # 3:1 ratio (map:legend)

with col1:
    # Initialize Map (existing code)
    m = folium.Map(location=[20, 10], zoom_start=2, min_zoom=2, tiles="OpenStreetMap")

    # Add tectonic plates (existing code)
    if not plate_boundaries.empty:
        folium.GeoJson(
            plate_boundaries,
            name="Tectonic Plates",
            style_function=lambda feature: {
                "color": "white",
                "weight": 1,
                "opacity": 0.5,
            },
        ).add_to(m)

    # --------------------------
    # EARTHQUAKE MARKERS (Circles)
    # --------------------------
    # Store min and max magnitude for the legend
    min_magnitude = earthquakes_with_plates['mag'].min() if not earthquakes_with_plates.empty else 0
    max_magnitude = earthquakes_with_plates['mag'].max() if not earthquakes_with_plates.empty else 10
    
    if not earthquakes_with_plates.empty:
        # Earthquake colormap (red-yellow for magnitude)
        eq_colormap = cm.linear.YlOrRd_09.scale(min_magnitude, max_magnitude)
        
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
                radius=1.5 * row['mag'],  # Larger circles for bigger quakes
                color=eq_colormap(row['mag']),
                fill=True,
                weight=1,
                fill_opacity=0.8,
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
                fill_color='yellow',  # Red color
                color='#8B8000',  # Darker border
                weight=1,
                fill_opacity=0.9,
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"Volcano: {row['volcano_name']} ({row['elevation']})"
            ).add_to(m)

    # Display the map (without the colormap legend)
    st_folium(m, width='100%', height=600)

# Create the legend in the second column
with col2:
    st.markdown("#### Map Legend")
    
    st.markdown("""
    <style>
    .legend-item {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
    }
    .circle-symbol {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background-color: #ff7800;
        display: inline-block;
        margin-right: 10px;
    }
    .triangle-symbol {
        width: 0;
        height: 0;
        border-left: 6px solid transparent;
        border-right: 6px solid transparent;
        border-bottom: 12px solid yellow;
        display: inline-block;
        margin-right: 10px;
    }
    .line-symbol {
        width: 20px;
        height: 3px;
        background-color: white;
        display: inline-block;
        margin-right: 10px;
    }
    </style>
    
    <div class="legend-item">
        <div class="circle-symbol"></div>
        <span>Earthquake</span>
    </div>
    
    <div class="legend-item">
        <div class="triangle-symbol"></div>
        <span>Volcano</span>
    </div>
    
    <div class="legend-item">
        <div class="line-symbol"></div>
        <span>Tectonic Plate</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    
    # Add custom colormap for earthquake magnitudes using matplotlib
    st.markdown("###### Earthquake Magnitude (Mw)")
    
    # Create a matplotlib figure for the colorbar
    fig, ax = plt.subplots(figsize=(4, 0.6))
    
    # Create a gradient similar to the YlOrRd colormap
    cmap = plt.cm.YlOrRd
    norm = mcolors.Normalize(vmin=min_magnitude, vmax=max_magnitude)
    
    # Create the colorbar
    cb = plt.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), 
                     cax=ax, orientation='horizontal')
    cb.set_label('Magnitude (Mw)')
    
    # Display the colorbar
    st.pyplot(fig)
        
    st.write("Darker circles indicate higher magnitude earthquakes.")


col1, col2 = st.columns([1,1])  # 3:1 ratio (map:legend)

with col1:
    st.markdown("##### 10 most recent seismic activity")
    earthquakes_display = earthquakes_with_plates.copy()
    earthquakes_display['datetime'] = pd.to_datetime(earthquakes_with_plates['datetime']).dt.strftime('%Y %b %d') 
    
    # Create a function to highlight only the first row
    def highlight_first_row(x):
        return ['background-color: rgba(100, 100, 255, 0.7)' if i == 0 else '' for i in range(len(x))]
    
    st.dataframe(earthquakes_display.head(10)[['datetime', 'place', 'mag', 'depth']]
                 .rename(columns={"datetime": "Date", "place": "Place", "tectonic_plate": "Tectonic Plate", "mag":"Magnitude (Mw)", "depth": "Depth (km)"})
                 .style.apply(highlight_first_row, axis=0)  # Apply the highlight function
                 .format("{:.2f}", subset=['Magnitude (Mw)'])
                 .format("{:.4f}", subset=['Depth (km)']),
                 hide_index=True)  # Hide the index

with col2:
    st.markdown("##### 10 most recent volcanic eruptions")
    
    # Similar highlighting function for volcanic data
    def highlight_first_row(x):
        return ['background-color: rgba(255, 100, 100, 0.7)' if i == 0 else '' for i in range(len(x))]
    
    st.dataframe(volcanic_weekly_report.head(10)[['start_date', 'volcano_name', 'volcano_type', 'elevation']]
                 .rename(columns = {
                 "start_date": "Date",
                 "volcano_name": "Volcano", 
                 "volcano_type": "Volcano Type", 
                 "elevation": "Elevation (m)"})
                .style.apply(highlight_first_row, axis=0)  # Apply the highlight function
                .format({'Elevation (m)': '{:.0f}'}),
                hide_index=True)  # Hide the index

st.divider()

######### MOST RECENT SEISMIC ACTIVITY
# Get the most recent earthquake
most_recent_place = earthquakes_with_plates.iloc[0]["place"]
most_recent_datetime = earthquakes_with_plates.iloc[0]["datetime"]
most_recent_mag = earthquakes_with_plates.iloc[0]["mag"]
most_recent_depth = earthquakes_with_plates.iloc[0]["depth"]
most_recent_plate = earthquakes_with_plates.iloc[0]["tectonic_plate"]

st.markdown(f"### The most recent seismic activity was registered **{most_recent_place}**")
st.subheader(f"On {most_recent_datetime}")

# Create a multi-column layout
col1, col2 = st.columns([1, 2])

with col1:
    st.metric(label="Magnitude", value=f"{most_recent_mag} Mw", border=True)
    st.metric(label="Depth", value=f"{most_recent_depth} Km", border=True)
    st.metric(label="Tectonic Plate", value=f"{most_recent_plate}", border=True)

with col2:
        # Create a light-themed Folium map
    m = folium.Map(
        location=[earthquakes_with_plates.iloc[0]['latitude'], earthquakes_with_plates.iloc[0]['longitude']],
        tiles="OpenStreetMap",  # Light theme
        zoom_start=5
    )
    # Add a marker for the volcano
    folium.CircleMarker(
        [earthquakes_with_plates.iloc[0]['latitude'], earthquakes_with_plates.iloc[0]['longitude']],
        radius=3,  # Larger circles for bigger quakes
        color='red',
        fill=True,
        fill_color='red',
        fill_opacity=1
    ).add_to(m)
    # Display the map (height matches the image)
    st_folium(m, height=348, width='100%')  # Adjust width as needed

st.divider()

######### MOST RECENT VOLCANIC ACTIVITY
if not volcanic_weekly_report.empty:
    # Get the most recent volcano
    most_recent_volcano = volcanic_weekly_report.iloc[0]["volcano_name"]
    most_recent_startdate = volcanic_weekly_report.iloc[0]["start_date"]
    most_recent_status = volcanic_weekly_report.iloc[0]["report_status"]
    most_recent_volcano_image = volcanic_weekly_report.iloc[0]["volcano_image"]
    most_recent_volcano_type = volcanic_weekly_report.iloc[0]["volcano_type"]
    most_recent_elevation = volcanic_weekly_report.iloc[0]["elevation"]

    st.markdown(f"### ({most_recent_status}) **{most_recent_volcano}**'s eruption is the latest one being registered")
    st.subheader(f"{most_recent_startdate}")

    # Create a multi-column layout
    col1, col2 = st.columns([1, 2])

    with col1:
        st.metric(label="Primary type", value=f"{most_recent_volcano_type}", border=True)
        st.metric(label="Elevation", value=f"{most_recent_elevation} m", border=True)
        img_src = get_image_base64(most_recent_volcano_image) or most_recent_volcano_image
        st.markdown(f'<img src="{img_src}" style="width:100%; border-radius:8px;">', unsafe_allow_html=True)

    with col2:
        # Create a light-themed Folium map
        m = folium.Map(
            location=[volcanic_weekly_report.iloc[0]['latitude'], volcanic_weekly_report.iloc[0]['longitude']],
            tiles="OpenStreetMap",  # Light theme
            zoom_start=5
        )
        # Add a marker for the volcano
        folium.CircleMarker(
            [volcanic_weekly_report.iloc[0]['latitude'], volcanic_weekly_report.iloc[0]['longitude']],
            radius=3,  # Larger circles for bigger quakes
            color='red',
            fill=True,
            fill_color='red',
            fill_opacity=1,
            tooltip="Volcano Location"
        ).add_to(m)
        # Display the map (height matches the image)
        st_folium(m, height=517, width='100%')  # Adjust width as needed
else:
    st.info("Volcanic activity data is currently unavailable.")
