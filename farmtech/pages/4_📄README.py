import requests
import streamlit as st


content = requests.get('https://raw.githubusercontent.com/vmmuthu31/farmtech/master/README.md').text
st.markdown(content, unsafe_allow_html=True)