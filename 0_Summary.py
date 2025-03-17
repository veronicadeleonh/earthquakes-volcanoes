import streamlit as st
import folium
from streamlit_folium import st_folium
import branca.colormap as cm

from utils.utils import load_earthquake_data, load_plate_boundaries, get_tectonic_plate_data

# Page Config
st.set_page_config(
    layout="wide",
    initial_sidebar_state="auto",
    page_title="Seismic Data",
    page_icon="🌍💥"
)

# Cache Data Loading
@st.cache_data
def get_earthquake_data():
    return load_earthquake_data()

@st.cache_data
def get_plate_boundaries_data():
    return load_plate_boundaries()

# Load Data (cached)
earthquakes_df = get_earthquake_data()
plate_boundaries = get_plate_boundaries_data()
earthquakes_with_plates = get_tectonic_plate_data(earthquakes_df)


## Header
st.title("Earthquakes 🌍💥")


######### MOST RECENT SEISMIC ACTIVITY
# Get the most recent earthquake
most_recent_place = earthquakes_with_plates.iloc[0]["place"]
most_recent_datetime = earthquakes_with_plates.iloc[0]["datetime"]
most_recent_mag = earthquakes_with_plates.iloc[0]["mag"]
most_recent_depth = earthquakes_with_plates.iloc[0]["depth"]

st.divider()
st.text(f"Most recent seismic activity registered")
st.subheader(f"{most_recent_place}")

# Create a multi-column layout
col1, col2, col3 = st.columns(3)

# Display the most recent earthquake details
with col1:
    st.metric(label="Date & Time", value=most_recent_datetime, border=True)

with col2:
    st.metric(label="Magnitude", value=f"{most_recent_mag} Mw", border=True)

with col3:
    st.metric(label="Depth", value=f"{most_recent_depth} Km", border=True)

st.divider()
######### FILTER TECTONIC PLATE
# Filters
st.subheader("Latest seismic activity map")
selected_tectonic_plates = st.multiselect("Filter by Minor Plate:", ["All"] + earthquakes_with_plates["tectonic_plate"].unique().tolist(), default="All")

# Filter the DataFrame based on selected tectonic plates
if "All" in selected_tectonic_plates:
    filtered_earthquakes = earthquakes_with_plates  # Include all plates
else:
    filtered_earthquakes = earthquakes_with_plates[
        earthquakes_with_plates["tectonic_plate"].isin(selected_tectonic_plates)
    ]

######## MAP

# Initialize Map
m = folium.Map(location=[20, 0], zoom_start=2, min_zoom=2, tiles="Esri.WorldImagery")

# Check if data exists before adding layers
if not plate_boundaries.empty:
    folium.GeoJson(
        plate_boundaries,
        name="Tectonic Plates",
        style_function=lambda feature: {
            "color": "blue",
            "weight": 1,
            "opacity": 0.5,
        },
    ).add_to(m)

# Only add earthquake markers if filtered data exists
if len(filtered_earthquakes) > 0:
    colormap = cm.linear.YlOrRd_09.scale(filtered_earthquakes['mag'].min(), filtered_earthquakes['mag'].max())

    for _, row in filtered_earthquakes.iterrows():
        color = colormap(row['mag'])  # Get color based on magnitude
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=2,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=f"Magnitude: {row['mag']} Mw. Date: {row["datetime"]}"
        ).add_to(m)

    # Add color legend
    colormap.caption = "Earthquake Magnitude in Moment Magnitude Scale (Mw)"
    m.add_child(colormap)

# Always add LayerControl even if map is empty
folium.LayerControl().add_to(m)

# If no data, show message
if plate_boundaries.empty and earthquakes_with_plates.empty:
    st.warning("No data available for the selected filters. Try selecting different plates.", icon="⚠️")


# Display map in Streamlit
st_folium(m, width='100%', height=500)


########## TOP 10 SEISMIC ACTIVITY BY MAGNITUDE AND DEPTH

# Top 10 seismic activity by magnitude and depth
st.write("Top 10 seismic activity by magnitude and depth")
st.dataframe(earthquakes_with_plates[['place', 'tectonic_plate', 'mag', 'depth']]
             .sort_values(by=["mag", "depth"], ascending=False)
             .head(10)
             .reset_index()
             .drop(["index"], axis=1)
             .rename(columns={"place": "Place", "tectonic_plate": "Tectonic Plate", "mag":"Magnitude (Mw)", "depth": "Depth (Km)"})
             .style.background_gradient(cmap='plasma'))