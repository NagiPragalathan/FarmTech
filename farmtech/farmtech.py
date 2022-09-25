import altair as alt
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
import requests
import utils.functions as functions
import utils.extract_isdasoil as isdasoil


# Config
functions.initialise_app()
point = st.session_state['point']
vicinity = st.session_state['vicinity']
location = functions.reverse_geocode(point)
country = location['address']['country']
country_code = location['address']['country_code']


# Immutable variables
if 'ASSETS' not in st.session_state:
    st.session_state['ASSETS'] = isdasoil.get_isdasoil_assets()

DATASET_ID_MAPPING = {
    'Fertility Capability Classification': 'fcc',
    'Total Nitrogen': 'nitrogen_total',
    'Soil Phosphorous': 'phosphorous_extractable',
    'Soil Potassium': 'potassium_extractable',
    'Soil pH': 'ph'
}


# Functions
def cal_no_constraints(df, cols_list):
    # calculates the % of land with no constraints
    filtered_df = df.copy()
    for col in cols_list:
        filtered_df = filtered_df.loc[(filtered_df[col] == 0)]
    
    filtered_len = len(filtered_df)
    total_rows = len(df)
    no_constraints_percent = (filtered_len/total_rows) * 100

    return no_constraints_percent


def cal_growable_mods(df, modifiable_cols_list, fcc_cols_list):
    df = df.copy()
    for col in modifiable_cols_list:
        df[col] = 0
    
    value = cal_no_constraints(df, fcc_cols_list)
    return value


# Data extraction and transformation
df = pd.DataFrame([], columns=['x_idx', 'y_idx'])

for dataset in DATASET_ID_MAPPING.keys():
    dataset_id = DATASET_ID_MAPPING[dataset]
    data_arr = isdasoil.get_point_data(dataset_id, point, vicinity)
    temp_df = pd.DataFrame(data_arr[0])
    temp_df = temp_df.stack()
    temp_df = temp_df.reset_index()
    temp_df.columns = ['x_idx', 'y_idx', dataset]
    df = df.merge(temp_df, how='outer', on=['x_idx', 'y_idx'])

## Join with FCC mapping
fcc_mapping_df = isdasoil.get_fcc_mapping()
df = df.merge(fcc_mapping_df, how='left', left_on='Fertility Capability Classification', right_on='fcc_value')
df = df.drop('fcc_value', axis=1)
df = df.rename({'fcc_description': 'FCC Constraints'}, axis=1)

## Temp and rainfall
temp = functions.extract_country_weather(country_code, 'temp')
rainfall = functions.extract_country_weather(country_code, 'rainfall')

## Crop
crop_df = pd.read_csv("./data/crop_attributes.csv")
crop_desc_df = pd.read_csv("./data/crops.csv")

st.markdown("# Farm-Tech")


col1, col2 = st.columns(2)

with col1:
    st.markdown(f"Location: **Chennai, TamilNadu, India**, Vicinity: **{vicinity}m**") 

with col2:
    with st.expander('Show location data'):
        URL = 'https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}'
        lat_lon=(10.9094334,78.3665347)
        r = requests.get(URL.format(lat=lat_lon[0],lon=lat_lon[1]))

        tndata = r.json()
        st.json(tndata)


st.markdown('## Environment')
with st.expander('Show raw data per plot'):
    cols_to_show = ['x_idx', 'y_idx', 'Soil Phosphorous', 
                    'Soil Potassium', 'Soil pH', 'FCC Constraints']
    st.dataframe(df[cols_to_show])


col1, col2 = st.columns(2)

with col1:
    option = st.selectbox('Select dataset to plot on map:', DATASET_ID_MAPPING.keys())
    dataset_id = DATASET_ID_MAPPING[option]

    if option != 'Fertility Capability Classification':
        geo_json = isdasoil.get_point_geojson(dataset_id, point, vicinity)

        plot_df = df[['x_idx', 'y_idx', option]]
    else:
        # Plot number of constraints instead
        option = 'Number of FCC Constraints'
        df[option] = df[list(isdasoil.FCC_CONSTRAINTS_DICT.keys())].sum(axis=1)
        plot_df = df[['x_idx', 'y_idx', option]]

        temp_arr = plot_df.set_index(['x_idx', 'y_idx']).unstack(level=-1).values
        geo_json = isdasoil.get_point_geojson(dataset_id, point, vicinity, data_arr=temp_arr)

    plot_df = plot_df.copy()
    plot_df['id'] = plot_df['x_idx'].astype('str') + '|' + plot_df['y_idx'].astype('str')

    # Plot map
    zoom_start = 17 + int(vicinity / 1000)
    tn_location=(10.9094334,78.3665347)
    indian_map = folium.Map(location=tn_location, zoom_start=zoom_start)

    folium.Choropleth(
        geo_data=geo_json,
        name=dataset_id,
        data=plot_df,
        columns=['id', option],
        key_on="feature.id",
        fill_color="Greens",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=option
    ).add_to(indian_map)

    folium.Marker(tn_location, tooltip='Selected Point').add_to(indian_map)
    folium.LayerControl().add_to(indian_map)
    st_folium(indian_map)

with col2:
    for col in ['Total Nitrogen', 'Soil Phosphorous', 'Soil Potassium', 'Soil pH']:
        subset = df[[col]]
        chart = alt.Chart(subset, title=col).mark_bar().encode(
            alt.X(col, bin=True),
            y='count()',
            tooltip='count()'
        ).properties(
            height=200
        ).interactive()
        st.altair_chart(chart, use_container_width=True)

# FCC Constraints
perc_no_constraints = cal_no_constraints(df, list(isdasoil.FCC_CONSTRAINTS_DICT.keys()))
perc_no_constraints_after_mods = cal_growable_mods(df, isdasoil.FCC_MODIFIABLE_CONSTRAINTS, list(isdasoil.FCC_CONSTRAINTS_DICT.keys()))
perc_diff = perc_no_constraints_after_mods - perc_no_constraints

col1, col2, col3 = st.columns([1, 1, 2])
col1.metric('Growable Land', str(round(perc_no_constraints, 2)) + '%')
col2.metric('Growable Land (after Modifications)', str(round(perc_no_constraints_after_mods, 2)) + '%', str(round(perc_diff, 2)) + '%')

constraints_df = df[list(isdasoil.FCC_CONSTRAINTS_DICT.keys())].copy()
constraints_counts = constraints_df.sum().sort_values(ascending=False).to_dict()
num_plots = df.shape[0]

with col3:
    constraints_counts_df = pd.DataFrame(constraints_counts.values(), index=constraints_counts.keys()).reset_index()
    constraints_counts_df.columns = ['Constraint', '% Land']
    constraints_counts_df = constraints_counts_df.loc[constraints_counts_df['% Land'] > 0]
    constraints_counts_df['Constraint'] = constraints_counts_df['Constraint'].map(isdasoil.FCC_CONSTRAINTS_DICT)
    constraints_counts_df['% Land'] = constraints_counts_df['% Land'] / num_plots * 100
    constraints_counts_df = constraints_counts_df.sort_values('% Land', ascending=False)
    chart = alt.Chart(constraints_counts_df, title='% Land per FCC Constraint').mark_bar().encode(
        x=alt.X('Constraint', sort=constraints_counts_df['Constraint'].values, axis=alt.Axis(labelAngle=-30)),
        y='% Land',
        tooltip=['Constraint', '% Land']
    ).interactive()
    st.altair_chart(chart, use_container_width=True)

with st.expander('Proposed Modifications'):
    
    for constraint in constraints_counts.keys():
        num_plots_affected = constraints_counts[constraint]
        if (num_plots_affected > 0) and (constraint in isdasoil.FCC_MODIFIABLE_CONSTRAINTS):
            st.markdown(f"""
                **{isdasoil.FCC_CONSTRAINTS_DICT[constraint]}** ({round(num_plots_affected / num_plots * 100, 2)}% affected)
            """)
            content = open('./data/mods/' + constraint + '.md', 'r', encoding='utf8')
            content = content.read()
            st.markdown(content, unsafe_allow_html=True)
            st.markdown(f"""
                ---
            """)


st.markdown('## Weather')
col1, col2 = st.columns(2)

with col1:
    c = functions.hover_line_chart(data=rainfall.T.reset_index(), x='index', y='rainfall',
                                   x_title="Month", y_title='Total Rainfall (mm)',
                                   title=f"Forecasted Rainfall in TamilNadu for 2023")
    st.altair_chart(c, use_container_width=True)

with col2:
    c = functions.hover_line_chart(data=temp.T.reset_index(), x='index', y='temp',
                                   x_title="Month", y_title='Average Temp (C)',
                                   title=f"Forecasted Monthly Temperature in TamilNadu for 2023")
    st.altair_chart(c, use_container_width=True)


st.markdown('## Crop Recommendations')

recommendation_df = functions.recommend_crops(df, crop_df, temp, rainfall)

if recommendation_df.shape[0] == 0:
    st.markdown('There are no crops to recommend for this area.')
else:
    col1, col2, col3, col4 = st.columns([1, 4, 2, 2])
    with col1:
        st.markdown('**Crop**')
    with col2:
        st.markdown('**Description**')
    with col3:
        st.markdown('**Suitability**')
    with col4:
        st.markdown('**Adjustments**')

    for _, row in recommendation_df.iterrows():
        crop = row['Crop']
        suitable = list(filter(lambda col: row[col] == 'optimal', row.keys()))
        adjustments = list(filter(lambda col: (row[col] != 'optimal') and (col not in ['Crop', 'num_suitable']), row.keys()))

        col1, col2, col3, col4 = st.columns([1, 4, 2, 2])
        with col1:
            url = crop_desc_df.loc[crop_desc_df['Crop'] == crop]['URL'].item()
            st.image(url, use_column_width='always')
            st.markdown(crop)
        with col2:
            desc = crop_desc_df.loc[crop_desc_df['Crop'] == crop]['Description'].item()
            st.markdown(desc)
        with col3:
            for feature in suitable:
                st.markdown(f"- This area has optimal levels of **{feature}** for {crop}")
        with col4:
            for feature in adjustments:
                value = recommendation_df.loc[recommendation_df['Crop'] == crop, feature].values[0]
                with st.expander(str(value).capitalize() + ' ' + feature):
                    content = open('./data/adjs/' + feature.lower() + '_' + value + '_summary.md', 'r', encoding='utf8')
                    content = content.read()
                    st.markdown(content, unsafe_allow_html=True)
        
        st.markdown('---')

st.markdown('## Places to Purchase Farming Supplies')

with st.expander('Stores in TamilNadu'):
    places_df = pd.read_csv('./data/farming_supplies_places.csv')
    filtered_df = places_df.loc[places_df['Country'] == "Chennai"]

    if filtered_df.shape[0] > 0:
        st.dataframe(filtered_df)
    else:
        st.markdown('No stores found in TamilNadu. Do check with your local communities.')