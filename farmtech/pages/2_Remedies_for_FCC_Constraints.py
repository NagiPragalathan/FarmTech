import streamlit as st

import utils.extract_isdasoil as isdasoil

st.title('Remedies for FCC Constraints')

st.markdown("""
    The following are the constraints for the iSDAsoil's
    implementation of the Fertility Capability Classification (FCC)
    framework, along with their correponding remedies.
    
    For more information on how the constraints are being
    identified for each plot, visit https://agricoop.nic.in/en/all-india-crop-situation
""")

for constraint_key in isdasoil.FCC_CONSTRAINTS_DICT:
    constraint = isdasoil.FCC_CONSTRAINTS_DICT[constraint_key]
    with st.expander(constraint):
        content = open('./data/mods/' + constraint_key + '.md', 'r', encoding='utf8')
        content = content.read()
        st.markdown(content, unsafe_allow_html=True)