# from folium.plugins import Draw
from folium.plugins import Draw
from shapely.geometry import LineString
from streamlit_folium import st_folium
import folium
import pandas as pd
import streamlit as st

import utils.extract_isdasoil as isdasoil
import utils.functions as functions



vicinity = st.slider('Select area (in metres): ', min_value=0, max_value=3000, value=300)
st.session_state['vicinity'] = vicinity

col1, col2 = st.columns(2)

with col1:
    # Render map
    tn_location=(10.9094334,78.3665347)
    map = folium.Map(location=tn_location, width='50%', zoom_start=7)
    st.info('Click on your location on the map')
    selected_point = st_folium(map, height=500)

with col2:
    if selected_point['last_clicked']:
        tn_location = (selected_point['last_clicked']['lat'], selected_point['last_clicked']['lng'])
        st.session_state['is_selected'] = True
        st.session_state['point'] = tn_location

    res = functions.reverse_geocode(tn_location)

    if st.session_state['is_selected']:
        st.success(f"You selected: **{res['display_name']}**") 
        tooltip = 'Selected Point'
    else:
        st.info(f"Current location: **{res['display_name']}**")
        tooltip ='Default Point'
    
    map = folium.Map(location=tn_location, zoom_start=10)
    folium.Marker(tn_location, tooltip=tooltip).add_to(map)
    st_folium(map, height=500)