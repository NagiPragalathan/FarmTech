import streamlit as st

import utils.extract_isdasoil as isdasoil

st.title('Soil Adjustments')

st.markdown("""
    The following are some features used for the crop recommender
    (excluding sodium). Adjustments to the soil conditions (depending
    on whether it is too high or too low), are detailed in this page.
""")

col1, col2 = st.columns(2)

feature_dict = {
    'ph': 'pH',
    'sodium': 'Sodium',
    'potassium': 'Potassium',
    'phosphorus': 'Phosphorus',
    'rainfall': 'Rainfall'
}

with col1:
    st.markdown('Too High')
    for feature_key in feature_dict:
        feature = feature_dict[feature_key]
        with st.expander(feature):
            content = open('./data/adjs/' + feature_key + '_high.md', 'r', encoding='utf8')
            content = content.read()
            st.markdown(content, unsafe_allow_html=True)

with col2:
    st.markdown('Too Low')
    for feature_key in feature_dict:
        feature = feature_dict[feature_key]
        with st.expander(feature):
            content = open('./data/adjs/' + feature_key + '_low.md', 'r', encoding='utf8')
            content = content.read()
            st.markdown(content, unsafe_allow_html=True)