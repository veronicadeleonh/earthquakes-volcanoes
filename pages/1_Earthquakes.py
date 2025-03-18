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
earthquakes_df, start_date = get_earthquake_data()
plate_boundaries = get_plate_boundaries_data()
earthquakes_with_plates = get_tectonic_plate_data(earthquakes_df)


## Header
st.title("Earthquakes 🌍💥")

######### FILTER TECTONIC PLATE
# Filters
st.subheader("Latest Seismic Activity Map")

start_date = start_date.strftime("%d.%m.%Y at %H:%M:%S")

st.markdown(
    f"""
    Explore the latest seismic activity recorded worldwide. This map visualizes earthquakes with a magnitude of **3.0 Mw or higher**, captured from **{start_date}** to today.

    By analyzing this data, you can identify patterns in seismic activity, understand the distribution of earthquakes across tectonic plates, and gain insights into regions with higher seismic risk.
    
    The data is sourced in real-time from the **[USGS Earthquake Catalog API](https://earthquake.usgs.gov/fdsnws/event/1/)**, a reliable and comprehensive database maintained by the United States Geological Survey.
    """
)


selected_tectonic_plates = st.multiselect("Filter by Tectonic Plate:", ["All"] + earthquakes_with_plates["tectonic_plate"].unique().tolist(), default="All")

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
st.subheader("Top 10 seismic activity by Magnitude and Depth")

top_10_plates_by_magnitude = earthquakes_with_plates[['place', 'tectonic_plate', 'mag', 'depth']].sort_values(by=["mag", "depth"], ascending=False).head(10).reset_index(drop=True)
highest_magnitude_plate = top_10_plates_by_magnitude.iloc[0]["tectonic_plate"]
highest_magnitude_mw = top_10_plates_by_magnitude.iloc[0]["mag"]

highest_depth_index = top_10_plates_by_magnitude["depth"].idxmax()
highest_depth_plate = top_10_plates_by_magnitude.iloc[highest_depth_index]["tectonic_plate"]
highest_depth_km = top_10_plates_by_magnitude["depth"].max()

st.dataframe(top_10_plates_by_magnitude
             .rename(columns={"place": "Place", "tectonic_plate": "Tectonic Plate", "mag":"Magnitude (Mw)", "depth": "Depth (km)"})
             .style.background_gradient(cmap='plasma'))

st.markdown(
f"""
- **{highest_magnitude_plate}** is the tectonic plate with the highest recorded magnitude, reaching **{highest_magnitude_mw} Mw**
- Among the highest magnitude earthquakes, **{highest_depth_plate}** recorded the deepest event at **{highest_depth_km} km below the Earth's surface**.
"""
)

st.divider()

########## EARTHQUAKE DEPTH VS MAGNITUDE BY TECTONIC PLATE
st.subheader("Earthquake Depth vs Magnitude by Tectonic Plate")
magnitude_depth_by_plate = earthquakes_with_plates[['tectonic_plate', 'mag', 'depth']]

# Create an Altair scatter plot
chart = alt.Chart(magnitude_depth_by_plate).mark_circle(size=60).encode(
    x=alt.X('mag:Q', 
                scale=alt.Scale(domain=[3.0, 6.5]), 
                axis=alt.Axis(title='Magnitude (Mw)', values=[3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5])),
    y=alt.Y('depth:Q', 
                scale=alt.Scale(domain=[0, 700]), 
                axis=alt.Axis(title='Depth (km)', values=[0, 100, 200, 300, 400, 500, 600, 700])),
    color='tectonic_plate:N',  # Color by tectonic plate
    tooltip=['tectonic_plate', 'mag', 'depth']  # Add tooltips
).properties(
    width=800,  # Width of the chart
    height=500  # Height of the chart
)

# Display the chart in Streamlit
st.altair_chart(chart, use_container_width=True)

# Calculate dynamic values
deepest_earthquake = magnitude_depth_by_plate.loc[magnitude_depth_by_plate['depth'].idxmax()]
shallowest_earthquake = magnitude_depth_by_plate.loc[magnitude_depth_by_plate['depth'].idxmin()]

deepest_plate = deepest_earthquake['tectonic_plate']
deepest_depth = deepest_earthquake['depth']
deepest_magnitude = deepest_earthquake['mag']

shallowest_plate = shallowest_earthquake['tectonic_plate']
shallowest_depth = shallowest_earthquake['depth']
shallowest_magnitude = shallowest_earthquake['mag']


st.markdown(
    f"""
    - **Deepest Earthquake**: The deepest earthquake occurred in the **{deepest_plate} tectonic plate**, at a depth of **{deepest_depth:.1f} km** with a magnitude of **{deepest_magnitude:.1f} Mw**.
    - **Shallowest Earthquake**: The shallowest earthquake occurred in the **{shallowest_plate} tectonic plate**, at a depth of **{shallowest_depth:.1f} km** with a magnitude of **{shallowest_magnitude:.1f} Mw**.
    - **Shallow Earthquakes**: Shallow earthquakes (less than 100 km) with lower magnitudes (below 4.0 Mw) are most frequent in the **North American** and **Pacific tectonic plates**.
    - **Magnitude Distribution**: 
        - For magnitudes below **4.0 Mw**, earthquakes are tightly clustered, indicating consistent and well-recorded seismic activity.
        - For magnitudes above **4.0 Mw**, the distribution becomes more uniform, with data points spread across various tectonic plates.
    - **Data Density**: The **North American** and **Pacific plates** have the highest density of data points, suggesting better seismic monitoring in these regions.
    """
)

st.divider()

########## TSUNAMI ACTIVITY
st.header("Tsunami activity 🌊")

tsunami_data = earthquakes_with_plates[earthquakes_with_plates["tsunami"] == 1]

# Calculate key metrics
num_tsunamis = len(tsunami_data)
max_magnitude = tsunami_data["mag"].max()
min_depth = tsunami_data["depth"].min()
most_common_plate = tsunami_data["tectonic_plate"].mode().iloc[0]

# Display metrics in columns
col1, col2, col3, col4 = st.columns(4)
col1.metric("Number of Tsunamis", num_tsunamis, border=True)
col2.metric("Max Magnitude", f"{max_magnitude} Mw", border=True)
col3.metric("Min Depth", f"{min_depth} km", border=True)
col4.metric("Most Common Plate", most_common_plate, border=True)

st.subheader("Tsunami-Related Earthquake Locations")

# Create a folium map centered on the first tsunami location
tsunami_map = folium.Map(location=[tsunami_data["latitude"].iloc[0], tsunami_data["longitude"].iloc[0]], zoom_start=2, min_zoom=2, tiles="Esri.WorldImagery")

# Add markers for each tsunami-related earthquake
for _, row in tsunami_data.iterrows():
    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=2,
        color="yellow",
        popup=f"Magnitude: {row['mag']} Mw<br>Depth: {row['depth']} km",
    ).add_to(tsunami_map)

# Display the map in Streamlit
st_folium(tsunami_map, width="100%", height=300)

st.dataframe(tsunami_data[['place', 'tectonic_plate', 'mag', 'depth']]
             .rename(columns={"place": "Place", "tectonic_plate": "Tectonic Plate", "mag":"Magnitude (Mw)", "depth": "Depth (km)"})
             .reset_index(drop=True)
             .style.background_gradient(cmap='plasma')
             .hide()
             )

st.markdown(
    f"""
    - **Low Depth**: Tsunami-related earthquakes tend to occur at shallow depths, with the deepest event recorded at **{tsunami_data['depth'].max()} km**.
    - **Magnitude Range**: The magnitudes of these earthquakes range from **{tsunami_data['mag'].min()} Mw** to **{tsunami_data['mag'].max()} Mw**.
    - **Most Active Plate**: The **{most_common_plate}** plate has the highest number of tsunami-related earthquakes.
    - **Geographical Distribution**: Tsunami-related earthquakes are concentrated in regions with active tectonic boundaries, particularly near the **{most_common_plate}** plate.
    """
)

st.info("Depth values are measured in kilometers below the Earth's surface. Lower values indicate shallower earthquakes, which are more likely to generate tsunamis.", icon="ℹ️")