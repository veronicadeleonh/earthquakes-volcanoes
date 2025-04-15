import streamlit as st
import folium
from streamlit_folium import st_folium

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

@st.cache_data
def get_weekly_report():
    return load_weekly_report()

volcanic_weekly_report = get_weekly_report()

@st.cache_data
def get_yearly_report():
    return load_yearly_report()

volcanic_yearly_report = get_yearly_report()


################ Style functions
def color_report_status(val):
    if val == "New":
        return 'background-color: #f84528; color: #fff'
    elif val == "Continuing":
        return 'background-color: #fea546; color: #000'
    elif val == "Over":
        return 'background-color: #d3d3d3; color: #000'
    return ''


################ Yearly Report
st.title("🌋 Eruptions Report in 2025")
st.write("""
         The eruption occurrencies is scraped from the Global Volcanism Program's Weekly Report. 
         - Kaggle Dataset 1
         - Kaggle Dataset 2
""")

yearly_eruptions_map = folium.Map(location=[10, -160], zoom_start=2, min_zoom=2, tiles="Esri.WorldImagery", max_bounds=True)

# Add markers for each volcano
for _, row in volcanic_yearly_report.iterrows():
    popup_text = f"""
    <b>{row['volcano_name']}</b><br>
    Status: {row['status']}<br>
    Type: {row['volcano_type']}<br>
    Elevation: {row['elevation']} m
    """
    popup = folium.Popup(popup_text, max_width=300)

    # marker_size = row['max vei'] * 0.1

    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=1,
        color="yellow",
        fill=True,
        fill_color="yellow",
        fill_opacity=0.8,
        popup=popup,
        tooltip=f"{row['volcano_name']}",
    ).add_to(yearly_eruptions_map)

# Display the map in Streamlit
st.subheader("Volcano Eruptions ")
st_folium(yearly_eruptions_map, width="100%", height=500)



st.dataframe(volcanic_yearly_report[['volcano_name', 'eruption start date', 'eruption stop date', 'status', 'max vei', 'volcano_type']]
             .rename(columns = {
                 "volcano_name": "Volcano",
                 "country": "Country",
                 "eruption start date": "Start date",
                 "eruption stop date": "Stop date",
                 "status": "Report Status",
                 "max vei": "Max VEI",
                 "volcano_type": "Volcano Type"})
                 .style
                 .applymap(color_report_status, subset=['Report Status']))




################ Weekly Report
st.title("🌋 Weekly report")
st.write("""
         The eruption occurrencies is scraped from the Global Volcanism Program's Weekly Report. 
         - Kaggle Dataset 1
         - Kaggle Dataset 2
""")

weekly_eruptions_map = folium.Map(location=[10, -160], zoom_start=2, min_zoom=2, tiles="Esri.WorldImagery", max_bounds=True)

# Add markers for each volcano
for _, row in volcanic_weekly_report.iterrows():
    popup_text = f"""
    <b>{row['volcano_name']}</b><br>
    Status: {row['report_status']}<br>
    Type: {row['volcano_type']}<br>
    Elevation: {row['elevation']} m
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
        tooltip=f"{row['volcano_name']}",
    ).add_to(weekly_eruptions_map)

# Display the map in Streamlit
st.subheader("Weekly Volcano Eruptions Report")
st_folium(weekly_eruptions_map, width="100%", height=500)


st.dataframe(volcanic_weekly_report[["volcano_name", "start_date", "report_status", "volcano_type", "elevation"]]
             .rename(columns = {
                 "volcano_name": "Volcano",
                 "start_date": "Start date",
                 "report_status": "Report Status",
                 "volcano_type": "Volcano Type", 
                 "elevation": "Elevation (m)"}
             )
             .style
             .applymap(color_report_status, subset=['Report Status']))


