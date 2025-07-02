import streamlit as st
import ee
import geemap.foliumap as geemap
import datetime

# Authenticate and initialize Earth Engine
try:
    ee.Initialize()
except Exception as e:
    ee.Authenticate()
    ee.Initialize()

st.set_page_config(layout="wide")

# Country options
country_names = ['Saudi Arabia', 'Qatar', 'Bahrain', 'United Arab Emirates', 'Oman']

# Dataset configuration
datasets = {
    'NO₂': {
        'collection': "COPERNICUS/S5P/OFFL/L3_NO2",
        'band': 'tropospheric_NO2_column_number_density',
        'vis': {'min': 0, 'max': 0.0003, 'palette': ['black', 'purple', 'red', 'orange', 'yellow']}
    },
    'O₃': {
        'collection': "COPERNICUS/S5P/OFFL/L3_O3",
        'band': 'O3_column_number_density',
        'vis': {'min': 0.1, 'max': 0.2, 'palette': ['blue', 'cyan', 'green', 'yellow']}
    },
    'SO₂': {
        'collection': "COPERNICUS/S5P/OFFL/L3_SO2",
        'band': 'SO2_column_number_density',
        'vis': {'min': 0, 'max': 0.0005, 'palette': ['white', 'gray', 'blue']}
    },
    'CO': {
        'collection': "COPERNICUS/S5P/OFFL/L3_CO",
        'band': 'CO_column_number_density',
        'vis': {'min': 0, 'max': 0.02, 'palette': ['white', 'purple', 'red']}
    },
    'HCHO': {
        'collection': "COPERNICUS/S5P/OFFL/L3_HCHO",
        'band': 'tropospheric_HCHO_column_number_density',
        'vis': {'min': 0, 'max': 0.0004, 'palette': ['white', 'orange', 'red']}
    },
    'AOD': {
        'collection': "COPERNICUS/S5P/OFFL/L3_AER_AI",
        'band': 'absorbing_aerosol_index',
        'vis': {'min': -1, 'max': 3, 'palette': ['white', 'orange', 'red']}
    }
}

# Sidebar controls
selected_country = st.sidebar.selectbox("Select country", country_names)
selected_gas = st.sidebar.selectbox("Select gas", list(datasets.keys()))

# Date range selection
min_date = datetime.date(2018, 7, 1)  # Earliest S5P data
max_date = datetime.date.today()
def_date = datetime.date(2024, 6, 1)
start_date = st.sidebar.date_input("Start date", value=def_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("End date", value=def_date, min_value=min_date, max_value=max_date)
if start_date > end_date:
    st.sidebar.error("Start date must be before end date.")

# Legend for selected gas
legend = datasets[selected_gas]['vis']
palette = legend['palette']
min_val = legend['min']
max_val = legend['max']

st.sidebar.markdown('**Legend**')
legend_html = f'<div style="display: flex; align-items: center;">'
for color in palette:
    legend_html += f'<div style="width: 24px; height: 16px; background:{color}; margin-right:2px;"></div>'
legend_html += f'<span style="margin-left: 8px;">{min_val} to {max_val}</span></div>'
st.sidebar.markdown(legend_html, unsafe_allow_html=True)

# Time range
start = ee.Date('2024-06-01')
end = start.advance(1, 'day')

# Get country shape
def get_country_feature(name):
    return ee.FeatureCollection("FAO/GAUL/2015/level0").filter(ee.Filter.eq('ADM0_NAME', name))

country_shape = get_country_feature(selected_country)

# Get the mean image and clip to country
mean_image = ee.ImageCollection(datasets[selected_gas]['collection']) \
    .select(datasets[selected_gas]['band']) \
    .filterDate(start, end) \
    .mean() \
    .clip(country_shape)

# Create a mask from the country shape
country_mask = ee.Image.constant(1).clip(country_shape).mask()

# Apply the mask to the image
image = mean_image.updateMask(country_mask)

# Basemap selection
basemap_options = {"Satellite": "SATELLITE", "Normal": "ROADMAP"}
selected_basemap = st.sidebar.selectbox("Basemap", list(basemap_options.keys()))

# Create map
m = geemap.Map(center=[24.5, 46.5], zoom=5)
m.add_basemap(basemap_options[selected_basemap])
m.addLayer(image, datasets[selected_gas]['vis'], selected_gas)
m.addLayer(country_shape.style(color='white', fillColor='00000000'), {}, 'Country Border')

# Display
st.markdown(
    """
    <style>
        .main {
            max-width: 100px;
            margin-left: auto;
            margin-right: auto;
        }
        .main .block-container {
            padding-top: 0rem;
            padding-bottom: 0rem;
            padding-left: 0rem;
            border-radius: 12px;
            border: 2px solid #81a1c1;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            background: #18191A;
            max-width: 300px;
            margin-left: auto;
            margin-right: auto;
        }
        .css-18e3th9 { padding-top: 0rem; padding-bottom: 0rem; }
        body { background-color: #18191A; }
    </style>
    """,
    unsafe_allow_html=True
)
m.to_streamlit(width=1000,  height=500)
