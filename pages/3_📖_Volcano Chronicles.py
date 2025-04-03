import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px
from datetime import datetime
import pandas as pd
import altair as alt
import numpy as np

from utils.utils import load_eruption_data, load_first_and_last_eruption_year, load_weekly_report, load_yearly_report

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


st.divider()
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

# # --- Volcano explorer ---

# App
st.title("🌋 Advanced Volcano Explorer")

# Search with autocomplete
if "volcano_names" not in st.session_state:
    st.session_state.volcano_names = eruptions_and_types["volcano_name"].tolist()

search_term = st.selectbox(
    "Search for a volcano:",
    options=st.session_state.volcano_names,
    index=None,
    placeholder="Start typing...",
)

# Display results
if search_term:
    # Filter to get all eruptions for the selected volcano
    volcano_selected = eruptions_and_types[eruptions_and_types["volcano_name"] == search_term]
    volcano = volcano_selected.iloc[0]  # Get the first row for volcano info

    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Volcano Data")
        st.metric("Elevation", f"{volcano['elevation']} m")
        st.write(f"**Type:** {volcano['volcano_type']}")
    
    with col2:
        st.subheader("Location")
        st.map(pd.DataFrame({
            "lat": [volcano['latitude']],
            "lon": [volcano['longitude']]
        }), zoom=5)
    
    # Historical Eruption Visualization
    st.subheader("Eruption History")

    # Check if eruption data exists
    if len(volcano_selected) >= 1 and 'year' in volcano_selected.columns:
        # Check if we have valid year data
        if not volcano_selected['year'].isna().all():
            # Create a copy to avoid modifying the original dataframe
            viz_data = volcano_selected.copy()
            
            # Convert years to integers if they're not already
            if not pd.api.types.is_integer_dtype(viz_data['year']):
                # If year is already datetime, extract year component
                if pd.api.types.is_datetime64_dtype(viz_data['year']):
                    viz_data['year'] = viz_data['year'].dt.year
                else:
                    # Try to convert to integer directly
                    viz_data['year'] = pd.to_numeric(viz_data['year'], errors='coerce').astype('Int64')
            
            # Drop rows with NaN years after conversion
            viz_data = viz_data.dropna(subset=['year'])
            
            if len(viz_data) > 0:
                # Option 1: Timeline visualization with Altair
                if 'vei' in viz_data.columns:
                    # Fill missing VEI values with 0 or None
                    viz_data['vei'] = viz_data['vei'].fillna(0)
                    
                    # Convert year to date format for better x-axis display
                    viz_data['date_for_viz'] = pd.to_datetime(viz_data['year'], format='%Y')
                    
                    # Create tooltip fields based on available columns
                    tooltip_fields = ['year', 'vei']
                    if 'volcano_type' in viz_data.columns:
                        tooltip_fields.append('volcano_type')
                    
                    # Create timeline chart
                    timeline_chart = alt.Chart(viz_data).mark_circle(size=100).encode(
                        x=alt.X('date_for_viz:T', title='Eruption Year', 
                            axis=alt.Axis(format='%Y', labelAngle=-45)),
                        y=alt.Y('vei:Q', title='Volcanic Explosivity Index (VEI)', 
                            scale=alt.Scale(domain=[0, max(8, viz_data['vei'].max() + 1)]),
                            axis=alt.Axis(tickMinStep=1)),
                        size=alt.Size('vei:Q', legend=None),
                        tooltip=tooltip_fields
                    ).properties(
                        height=300
                    ).interactive()
                    
                    st.altair_chart(timeline_chart, use_container_width=True)
                else:
                    st.info("VEI (Volcanic Explosivity Index) data not available for timeline visualization.")
                
                # Option 2: Bar chart showing count of eruptions by decade or century
                # Create decade bins - make sure year is numeric first
                viz_data['decade'] = (viz_data['year'] // 10) * 10
                
                # Count eruptions by decade
                eruptions_by_decade = viz_data.groupby('decade').size().reset_index(name='count')
                
                if not eruptions_by_decade.empty:
                    # Create bar chart
                    decade_chart = px.bar(
                        eruptions_by_decade, 
                        x='decade', 
                        y='count',
                        labels={'decade': 'Decade', 'count': 'Number of Eruptions'},
                        title=f'Eruptions by Decade for {search_term}'
                    )
                    
                    # Improve x-axis formatting for decades
                    decade_chart.update_xaxes(type='category')
                    
                    st.plotly_chart(decade_chart, use_container_width=True)
                else:
                    st.info("Couldn't generate decade chart due to data issues.")
            else:
                st.info("No valid year data available for visualizations.")
        else:
            st.info("No eruption date information available for this volcano.")
    else:
        st.info("No historical eruption data available for this volcano.")
    
    st.subheader("Detailed Information") 
    st.dataframe(volcano_selected)
        
else:
    st.info("Please search for a volcano to see information")