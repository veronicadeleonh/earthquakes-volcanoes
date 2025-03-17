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
earthquakes_df = get_earthquake_data()
plate_boundaries = get_plate_boundaries_data()
earthquakes_with_plates = get_tectonic_plate_data(earthquakes_df)


## Header
st.title("Earthquakes 🌍💥")

######### FILTER TECTONIC PLATE
# Filters
st.subheader("Latest seismic activity map")
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
st.dataframe(earthquakes_with_plates[['place', 'tectonic_plate', 'mag', 'depth']]
             .sort_values(by=["mag", "depth"], ascending=False)
             .head(10)
             .reset_index(drop=True)
             .rename(columns={"place": "Place", "tectonic_plate": "Tectonic Plate", "mag":"Magnitude (Mw)", "depth": "Depth (Km)"})
             .style.background_gradient(cmap='plasma'))


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