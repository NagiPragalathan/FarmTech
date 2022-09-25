import altair as alt
import pandas as pd
import streamlit as st
import requests


def reverse_geocode(lat_lon):
    """
    Calls the Nominatim API to conduct reverse geocoding.
    See https://nominatim.org/release-docs/develop/api/Reverse/ for more.
    :param lat_lon: tuple of latitude and longitude of selected location
    :return: response: response in json format.
    """
    URL = 'https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}'
    r = requests.get(URL.format(lat=lat_lon[0],lon=lat_lon[1]))
    response = r.json()

    return response

def extract_country_weather(country_code, variable):
    """
    Given a country_code, extracts rainfall/temp data from csv and performs some preprocessing.
    :param country_code: String, state code (e.g. TN for Tamilnadu)
    :param variable: String, only either 'rainfall' or 'temp' accepted.
    :return:
    """
    if variable not in ['rainfall', 'temp']:
        raise Exception('not yet implemented')
    else:
        country_code = str.upper(country_code)
        df = pd.read_csv(f"data/weather/{variable}_forecasted.csv")
        df = df[df['country_code_alpha2'] == country_code].iloc[:,-12:].reset_index(drop=True)
        df.columns = pd.to_datetime(df.columns).date
        df.index=[variable]
        return df

def hover_line_chart(data,x,y,x_title, y_title, title):
    hover = alt.selection_single(
        fields=[x],
        nearest=True,
        on="mouseover",
        empty="none",
    )

    lines = (
        alt.Chart(data, title=title).mark_line().encode(
            alt.X(x, title=x_title),
            alt.Y(y, title=y_title)
        )
    )
    points = lines.transform_filter(hover).mark_circle(size=65)

    # Draw a rule at the location of the selection
    tooltips = (
        alt.Chart(data)
        .mark_rule()
        .encode(
            x=x,
            y=y,
            opacity=alt.condition(hover, alt.value(0.3), alt.value(0)),
            tooltip=[
                alt.Tooltip(x, title=x_title),
                alt.Tooltip(y, title=y_title),
            ],
        )
        .add_selection(hover)
    )
    return (lines + points + tooltips).interactive()

def initialise_app():
    # Config 
    st.set_page_config(page_title='Farmtech', 
                    page_icon='🌱',
                    layout='wide', 
                    initial_sidebar_state='expanded')

    if 'point' not in st.session_state:
        st.session_state['point'] = (-1.77595, 29.72785)

    if 'vicinity' not in st.session_state:
        st.session_state['vicinity'] = 300

    if 'is_selected' not in st.session_state:
        st.session_state['is_selected'] = False


def recommend_crops(env_df, crop_df, temp_df, rainfall_df):
    recommendation_df = crop_df[['Crop']].copy()

    soil_phos_avg = env_df["Soil Phosphorous"].mean()
    soil_pota_avg = env_df["Soil Potassium"].mean()
    soil_pH_avg = env_df["Soil pH"].mean()
    mean_temp = temp_df.mean(axis=1)[0]
    mean_rainfall = rainfall_df.mean(axis=1)[0]

    recommendation_df['potassium'] = _calculate_suitability(crop_df["min_potassium"], crop_df["max_potassium"], soil_pota_avg)
    recommendation_df['phosphorus'] = _calculate_suitability(crop_df["min_phosphorus"], crop_df["max_phosphorus"], soil_phos_avg)
    recommendation_df['pH'] = _calculate_suitability(crop_df["min_ph_soil"], crop_df["max_ph_soil"], soil_pH_avg)
    recommendation_df['temperature'] = _calculate_suitability(crop_df["min_temp"], crop_df["max_temp"], mean_temp)
    recommendation_df['rainfall'] = _calculate_suitability(crop_df["min_rainfall"], crop_df["max_rainfall"], mean_rainfall)

    recommendation_df['num_suitable'] = (recommendation_df == 'optimal').sum(axis=1)
    recommendation_df = recommendation_df.loc[(recommendation_df['num_suitable'] > 0) & (recommendation_df['temperature'] == 'optimal')]
    recommendation_df = recommendation_df.sort_values('num_suitable', ascending=False)

    return recommendation_df

def _calculate_suitability(min_series, max_series, available_amount):
    results = []
    for min_val, max_val in zip(min_series.values, max_series.values):
        if available_amount < min_val:
            results.append('low')
        elif available_amount > max_val:
            results.append('high')
        else:
            results.append('optimal')
    return results
