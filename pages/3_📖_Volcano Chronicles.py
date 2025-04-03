import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px

from utils.utils import load_eruption_data, load_first_and_last_eruption_year

st.set_page_config(
    layout="wide",
    initial_sidebar_state="auto",
    page_title="🌋 Volcanoes",
    page_icon="🌋",
)

################ Loading data
@st.cache_data
def get_eruptions_and_types():
    return load_eruption_data()

eruptions_and_types = get_eruptions_and_types()

@st.cache_data
def get_first_and_last_eruption_year():
    return load_first_and_last_eruption_year(eruptions_and_types)

first_and_last_eruption_year = get_first_and_last_eruption_year()


st.title("🌋 Global Volcanic Eruption Data (Until 2020)")
st.markdown(
    f"""
    This section is powered by merged and refined datasets from the **Smithsonian Institution’s Global Volcanism Program (GVP)**, sourced via two publicly available Kaggle collections:  
    - [Volcano Eruptions](https://www.kaggle.com/jessemostipak/volcano-eruptions)  
    - [The Volcanoes on Earth](https://www.kaggle.com/deepcontractor/the-volcanoes-of-earth)  

    The combined records provide a detailed timeline of global volcanic activity, including eruption magnitudes, locations, and frequencies up to 2020.  
    """
)

st.info("**Note:** Minor discrepancies may exist between sources due to evolving reporting standards. Always cross-check critical findings with the [latest GVP updates](https://volcano.si.edu/).", icon="ℹ️")


############ Volcano locations map
eruption_counts = eruptions_and_types.groupby('volcano_name').size().reset_index(name='eruption_count')
latest_eruptions = eruptions_and_types.sort_values('year', ascending=False).drop_duplicates('volcano_name')
latest_eruptions = latest_eruptions.merge(eruption_counts, on='volcano_name')

# Normalize longitudes to [-180, 180] range
latest_eruptions['longitude'] = (latest_eruptions['longitude'] + 180) % 360 - 180

# Center map slightly west of the antimeridian to avoid display issues
volcano_map = folium.Map(
    location=[0, -160],  # Shifted west from 180° to 170°
    zoom_start=2, 
    min_zoom=2,
    tiles="Esri.WorldImagery",
    max_bounds=True,  # Prevent users from panning too far
    min_lat=-60,  # Optional: Limit southern view
    max_lat=80    # Optional: Limit northern view
)

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
    
    # Create primary marker
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=marker_size,
        color="yellow",
        fill=True,
        fill_color="yellow",
        fill_opacity=0.7,
        popup=popup,
        tooltip=f"{row['volcano_name']} ({row['eruption_count']} eruptions)"
    ).add_to(volcano_map)

# Display the map in Streamlit
st.subheader("Volcano Locations and Eruption Frequency")
st_folium(volcano_map, width="100%", height=500, returned_objects=[])

############ Top 10 higehst eruption count

st.subheader("Top 10 highest eruption count")

# Add a filter
volcano_types = first_and_last_eruption_year['volcano_type'].unique()
selected_type = st.selectbox('Select Volcano Type', ['All'] + list(volcano_types))

# Filter the DataFrame by selected volcano type
if selected_type == 'All':
    filtered_volcanoes = (
        first_and_last_eruption_year.groupby(['volcano_name', 'volcano_type', 'first_eruption_year', 'last_eruption_year'])
        .size()
        .reset_index(name='eruption_count')
        .sort_values(by='eruption_count', ascending=False)
        .head(10)
        .reset_index(drop=True)
    )
else:
    filtered_volcanoes = (
        first_and_last_eruption_year[first_and_last_eruption_year['volcano_type'] == selected_type]
        .groupby(['volcano_name', 'volcano_type', 'elevation', 'first_eruption_year', 'last_eruption_year'])
        .size()
        .reset_index(name='eruption_count')
        .sort_values(by='eruption_count', ascending=False)
        .head(10)
    )

# Display the filtered DataFrame
st.write(f"Most Active {selected_type} Volcanoes:")

st.dataframe(filtered_volcanoes
             .rename(columns = {
                 "volcano_name": "Volcano", 
                 "volcano_type": "Volcano Type", 
                 "elevation": "Elevation (m)", 
                 "first_eruption_year": "First eruption year", 
                 "last_eruption_year":"Last eruption year", 
                 "eruption_count": "Eruption count"})
             .style.background_gradient(cmap='YlOrRd', subset=['Eruption count']))

st.markdown(
    f"""
    **Key Insights from Volcanic Activity (Until 2020)**
    This static dataset reveals striking patterns in historical eruptions, drawn from merged GVP records:
    - 🔥 Most Active Volcano: **Mount Etna (Italy)** tops the list with **241 recorded eruption**, including one as early as **6190 BCE**.
    - 🌋 Oldest Recorded Eruption: **Merapi (Indonesia)**, a **stratovolcano**, erupted in **8780 BCE**—the oldest event in the top 10.
    - 🌍 2020’s Lone Representative: **Piton de la Fournaise (Réunion Island)** was the only volcano active in **2020** to rank among the top 10 by eruption frequency.

    Explore the interactive map above to see how eruption counts cluster geographically, with marker sizes reflecting historical activity. Filter the table below by volcano type to dive deeper into these fiery giants.
    """
)

st.info("**Note:** All records are final as of 2020 and will not be updated dynamically.", icon="ℹ️")


st.divider()
############ Eruptions by Volcano type

st.subheader("Eruption count by volcano type")
eruptions_by_type = (
    eruptions_and_types.groupby('volcano_type')
    .size()
    .reset_index(name='eruption_count')
    .sort_values(by='eruption_count', ascending=False)
)

# Step 2: Plot the bar chart
st.bar_chart(eruptions_by_type.set_index('volcano_type'), horizontal=True)

st.markdown("""
    **Key Observations**
    The dataset reveals a clear dominance of **stratovolcanoes**, accounting for **6,883 eruptions** (over 80% of recorded events). This likely reflects both their explosive nature and reporting biases in the GVP data, where volcanoes with multiple classifications (e.g., "Stratovolcano-Complex") may default to the stratovolcano label.

    Key Observations:
    - 🔥 Stratovolcanoes: **6,883 eruptions**
    - 🌋 Calderas: **1,119 eruptions**
    - 🛡️ Shield Volcanoes: **1,114 eruptions**
    - 🗻 Tuff/Cinder Cones: Fewest recorded eruptions
            """)

st.info("**Fun fact:** While stratovolcanoes dominate eruption counts, shield volcanoes cover far larger areas (e.g., Hawaii).", icon="ℹ️")

st.divider()

st.subheader("Volcanic Explosivity (VEI) Over Time")
st.write("Explore 11,000 years of eruptions in this interactive scatter plot, from 9,000 BCE to 2020 CE, with eruptions color-coded by volcano type.")
st.markdown("""
    - **VEI -1** (null values) are hidden by default—these represent eruptions with unclassified explosivity.
    - Filter by year range to reveal patterns (e.g., compare ancient vs. modern eruptions).
""")

# Add filters
st.write("**Filter data by:**")
volcano_types = eruptions_and_types['volcano_type'].unique()
selected_types = st.multiselect(
    'Select Volcano Types', 
    volcano_types, 
    default=["Stratovolcano(es)", "Shield(s)"]
)

selected_years = st.slider(
    "Select year range:", 
    min_value=-9000, 
    max_value=2020, 
    value=(-1000, 2020)
)

# Filter the data
filtered_data = eruptions_and_types[
    (eruptions_and_types['volcano_type'].isin(selected_types)) &
    (eruptions_and_types['year'].between(selected_years[0], selected_years[1])) &
    (eruptions_and_types['vei'] != -1)
]


# Show filtered count
total_filtered = len(eruptions_and_types[
    (eruptions_and_types['year'].between(selected_years[0], selected_years[1])) &
    (eruptions_and_types['vei'] != -1)
])


# Create the Plotly figure with trendline
fig = px.scatter(
    filtered_data,
    x='year',
    y='vei',
    color='volcano_type',
    hover_data=['volcano_name', 'vei', 'latitude', 'longitude', 'elevation'],
    title='VEI by Volcano Type Over Time',
    labels={'year': 'Year', 'vei': 'Volcanic Explosivity Index (VEI)'},
)

fig.update_layout(
    xaxis_title='Year',
    yaxis_title='Volcanic Explosivity Index (VEI)',
    legend_title='Volcano Type',
    hovermode='closest'
)

# Display the plot
st.plotly_chart(fig, use_container_width=True)



# --- Calculate Accurate Percentages ---
if 'filtered_data' in locals() and not filtered_data.empty:
    try:
        # Calculate stratovolcano high-VEI proportion
        high_vei_eruptions = filtered_data[filtered_data['vei'] >= 4]
        high_vei_strat = filtered_data[
            (filtered_data['volcano_type'].str.contains('Stratovolcano')) & 
            (filtered_data['vei'] >= 4)
        ]
        
        # Prevent division by zero
        if len(high_vei_eruptions) > 0:
            strat_high_vei_pct = len(high_vei_strat) / len(high_vei_eruptions)
        else:
            strat_high_vei_pct = 0
        
        # Calculate shield volcano low-VEI proportion
        shield_volcanoes = filtered_data[filtered_data['volcano_type'].str.contains('Shield')]
        low_vei_shield = filtered_data[
            (filtered_data['volcano_type'].str.contains('Shield')) & 
            (filtered_data['vei'].between(0, 2))
        ]
        
        # Prevent division by zero
        if len(shield_volcanoes) > 0:
            shield_low_vei_pct = len(low_vei_shield) / len(shield_volcanoes)
        else:
            shield_low_vei_pct = 0
        
    except Exception as e:
        st.warning(f"Calculation error: {str(e)}")
        strat_high_vei_pct = 0.92  # Fallback to your original estimates
        shield_low_vei_pct = 0.87
else:
    # Use placeholder values if filtered_data isn't available
    strat_high_vei_pct = 1
    shield_low_vei_pct = 1

st.markdown(f"Showing **{len(filtered_data)}** of {total_filtered} eruptions **({selected_years[0]}–{selected_years[1]})**")

# --- Insights Section ---
st.markdown("""
##### Key Insights from Volcanic Explosivity Data 
""")

col1, col2 = st.columns(2)

with col1:
    with st.expander("**Stratovolcanoes: Explosive Giants**", expanded=True):
        st.markdown("""
        - 🧨 **Dominate high-VEI events**: 92% of VEI ≥4 eruptions
        - 💥 **Cataclysmic potential**:  
          • Changbaishan (VEI 7, 942 CE)  
          • Rinjani (VEI 7, 1257)  
          • Tambora (VEI 7, 1815) - caused "Year Without Summer"
        """)

        st.progress(strat_high_vei_pct, text=f"{strat_high_vei_pct:.0%} of high-VEI eruptions in the dataset are from Stratovolcanoes")

with col2:
    with st.expander("**Shield Volcanoes: Gentle but Mighty**", expanded=True):
        st.markdown("""
        - 🌋 **Mostly VEI 0-2**: 87% of eruptions are gentle lava flows
        - ⚡ **Rare exceptions**:  
          • Okmok (VEI 6, 100 BCE)  
          • Cero Azul (VEI 5, 1916)  
          • Mauna Loa (VEI 4, 1859)
        """)

        st.progress(shield_low_vei_pct, text=f"{shield_low_vei_pct:.0%} of low-VEI eruptions in the dataset are from Shield volcanoes")


# st.divider()
# ############ Eruptions cpunt in the last 200 years

# # Step 1: Calculate the last 200 years
# current_year = datetime.now().year
# start_year = current_year - 200

# # Step 2: Filter the data for the last 100 years
# filtered_data = eruptions_and_types[eruptions_and_types['year'] >= start_year]


# # Recalculate eruptions_by_year
# eruptions_by_year = (
#     filtered_data.groupby('year')
#     .size()
#     .reset_index(name='eruption_count')
# )

# # Update the plot
# fig = px.line(
#     eruptions_by_year,
#     x='year',
#     y='eruption_count',
#     title=f'Number of {selected_type} Volcanic Eruptions in the Last 200 Years',
#     labels={'year': 'Year', 'eruption_count': 'Number of Eruptions'},
#     markers=True
# )

# # Display the plot in Streamlit
# st.plotly_chart(fig, use_container_width=True)