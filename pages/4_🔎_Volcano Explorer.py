import streamlit as st
import plotly.express as px
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

st.warning('Page under construction', icon="🚧")

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
        st.write(f"**Primary Type:** {volcano['volcano_type']}")
        st.image(volcano['volcano_image'])
    
    with col2:
        st.subheader("Location")
        st.map(pd.DataFrame({
            "lat": [volcano['latitude']],
            "lon": [volcano['longitude']]
        }), zoom=5, height=410)
    
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
                # Try to convert to integer directly
                viz_data['year'] = pd.to_numeric(viz_data['year'], errors='coerce')
            
            # Drop rows with NaN years after conversion
            viz_data = viz_data.dropna(subset=['year'])
            
            if len(viz_data) > 0:
                # Display count of ancient vs modern eruptions
                ancient_count = len(viz_data[viz_data['year'] < 1675])
                modern_count = len(viz_data[viz_data['year'] >= 1675])
                total_count = len(viz_data)
                
                if ancient_count > 0:
                    st.info(f"This volcano has {total_count} recorded eruptions: {ancient_count} ancient (before 1675) and {modern_count} modern.")
                
                # Option 1: Timeline visualization using numeric years directly (not datetime)
                # This works for ANY year range
                if 'vei' in viz_data.columns:
                    # Fill missing VEI values with 0
                    viz_data['vei'] = viz_data['vei'].fillna(0)
                    
                    # Create tooltip fields based on available columns
                    tooltip_fields = ['year', 'vei']
                    if 'volcano_type' in viz_data.columns:
                        tooltip_fields.append('volcano_type')
                    
                    # Add BCE/CE notation for better readability
                    viz_data['year_display'] = viz_data['year'].apply(
                        lambda y: f"{abs(int(y))} BCE" if y < 0 else f"{int(y)} CE"
                    )
                    tooltip_fields.append('year_display')
                    
                    # Create timeline chart
                    timeline_chart = alt.Chart(viz_data).mark_circle(size=100).encode(
                        x=alt.X('year:Q', title='Eruption Year', 
                            axis=alt.Axis(labelAngle=-45)),
                        y=alt.Y('vei:Q', title='Volcanic Explosivity Index (VEI)', 
                            scale=alt.Scale(domain=[0, max(8, viz_data['vei'].max() + 1)]),
                            axis=alt.Axis(tickMinStep=1)),
                        size=alt.Size('vei:Q', legend=None),
                        tooltip=tooltip_fields
                    ).properties(
                        height=300,
                        width=600  # Give it more width for geological timescales
                    ).interactive()
                    
                    st.altair_chart(timeline_chart, use_container_width=True)
                    
                    # If we have a wide range of years, add a time period selector
                    year_range = viz_data['year'].max() - viz_data['year'].min()
                    if year_range > 1000:
                        st.write("Select time period to view:")
                        time_periods = [
                            "All Time",
                            "Last 100 Years",
                            "Last 1000 Years",
                            "Last 10,000 Years",
                            "BCE Only",
                            "CE Only"
                        ]
                        selected_period = st.selectbox("Time Period", time_periods, index=0)
                        
                        # Filter data based on selected time period
                        if selected_period == "Last 100 Years":
                            filtered_data = viz_data[viz_data['year'] > (2025 - 100)]
                        elif selected_period == "Last 1000 Years":
                            filtered_data = viz_data[viz_data['year'] > (2025 - 1000)]
                        elif selected_period == "Last 10,000 Years":
                            filtered_data = viz_data[viz_data['year'] > (2025 - 10000)]
                        elif selected_period == "BCE Only":
                            filtered_data = viz_data[viz_data['year'] < 0]
                        elif selected_period == "CE Only":
                            filtered_data = viz_data[viz_data['year'] >= 0]
                        else:  # All Time
                            filtered_data = viz_data
                        
                        if len(filtered_data) > 0:
                            # Create filtered timeline chart
                            filtered_chart = alt.Chart(filtered_data).mark_circle(size=100).encode(
                                x=alt.X('year:Q', title='Eruption Year'),
                                y=alt.Y('vei:Q', title='Volcanic Explosivity Index (VEI)'),
                                size=alt.Size('vei:Q', legend=None),
                                tooltip=tooltip_fields
                            ).properties(
                                height=300
                            ).interactive()
                            
                            st.write(f"Showing {len(filtered_data)} eruptions for: {selected_period}")
                            st.altair_chart(filtered_chart, use_container_width=True)
                        else:
                            st.write(f"No eruptions found for: {selected_period}")
                else:
                    st.info("VEI (Volcanic Explosivity Index) data not available for timeline visualization.")
                
                # Option 2: Bar chart showing count of eruptions by time periods
                # For geological timescales, decades may be too granular
                # Determine appropriate binning based on data range
                year_min = viz_data['year'].min()
                year_max = viz_data['year'].max()
                year_span = year_max - year_min
                
                # Choose appropriate binning
                if year_span > 100000:
                    # For very long timescales (100k+ years)
                    bin_size = 10000
                    bin_label = '10,000 Year Periods'
                elif year_span > 10000:
                    # For long timescales (10k-100k years)
                    bin_size = 1000
                    bin_label = 'Millennia'
                elif year_span > 1000:
                    # For medium timescales (1k-10k years)
                    bin_size = 100
                    bin_label = 'Centuries'
                else:
                    # For shorter timescales (<1k years)
                    bin_size = 10
                    bin_label = 'Decades'
                
                # Create bins based on chosen scale
                viz_data['time_bin'] = (viz_data['year'] // bin_size) * bin_size
                
                # Add BCE/CE notation
                viz_data['time_bin_label'] = viz_data['time_bin'].apply(
                    lambda y: f"{abs(int(y))}-{abs(int(y))+bin_size-1} BCE" if y < 0 
                    else f"{int(y)}-{int(y)+bin_size-1} CE"
                )
                
                # Count eruptions by time bin
                eruptions_by_period = viz_data.groupby(['time_bin', 'time_bin_label']).size().reset_index(name='count')
                eruptions_by_period = eruptions_by_period.sort_values('time_bin')
                
                if not eruptions_by_period.empty:
                    # Create bar chart
                    period_chart = px.bar(
                        eruptions_by_period, 
                        x='time_bin', 
                        y='count',
                        labels={'time_bin': bin_label, 'count': 'Number of Eruptions'},
                        title=f'Eruptions by {bin_label} for {search_term}',
                        hover_data=['time_bin_label']
                    )
                    
                    # Customize x-axis to make it more readable for geological timescales
                    period_chart.update_xaxes(
                        tickmode='array',
                        tickvals=eruptions_by_period['time_bin'].tolist(),
                        ticktext=eruptions_by_period['time_bin_label'].tolist(),
                        tickangle=-45
                    )
                    
                    st.plotly_chart(period_chart, use_container_width=True)
                else:
                    st.info("Couldn't generate time period chart due to data issues.")
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

#------ Sidebar
with st.sidebar:
    st.markdown("## Data Attribution")
    st.markdown("""
    - [Smithsonian GVP](https://volcano.si.edu/) data through 2020
    - Kaggle merged datasets
        - [Volcano Eruptions](https://www.kaggle.com/jessemostipak/volcano-eruptions)  
        - [The Volcanoes on Earth](https://www.kaggle.com/deepcontractor/the-volcanoes-of-earth)  
    """)
    
    st.markdown("---")
    st.markdown("""
    *Note: This app combines authoritative sources 
    with crowdsourced data for completeness.*
    """)