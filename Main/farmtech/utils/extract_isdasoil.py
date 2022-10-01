# Reference: https://github.com/iSDA-Africa/isdasoil-tutorial

from pyproj import Transformer
from pystac import Catalog
from shapely.geometry import Polygon
from shapely.ops import unary_union
import pandas as pd
import geojson
import numpy as np
import rasterio as rio
import streamlit as st


CONVERSION_FUNCS_DICT = {
    "x": np.vectorize(lambda x: x),
    "x/10": np.vectorize(lambda x: x/10, otypes=["float32"]),
    "x/100": np.vectorize(lambda x: x/100, otypes=["float32"]),
    "expm1(x/10)": np.vectorize(lambda x: np.expm1(x / 10), otypes=["float32"]),
    "%3000": np.vectorize(lambda x: int(x%3000), otypes=["int16"])
}
FCC_CONSTRAINTS_DICT = {
    'fcc_al_toxicity': 'Aluminium toxicity',
    'fcc_calcareous': 'Calcareous',
    'fcc_gravelly': 'Gravel',
    'fcc_high_erosion_risk_-_shallow_depth': 'High erosion risk: Shallow depth',
    'fcc_high_erosion_risk_-_steep_slope': 'High erosion risk: Steep slope',
    'fcc_high_erosion_risk_-_textual_contrast': 'High erosion risk - textual discontinuity',
    'fcc_high_leaching_potential': 'High leaching potential',
    'fcc_low_k': 'Low potassium reserves',
    'fcc_shallow': 'Shallow',
    'fcc_slope': 'Slope',
    'fcc_sulfidic': 'Sulfidic'
}
FCC_MODIFIABLE_CONSTRAINTS = ['fcc_al_toxicity', 'fcc_calcareous', 'fcc_gravelly', 
                                'fcc_high_leaching_potential', 'fcc_low_k', 'fcc_shallow',
                                'fcc_slope', 'fcc_sulfidic']

def get_isdasoil_assets():
    assets_dict = dict()

    print('Populating iSDAsoil assets...')
    catalog = Catalog.from_file("https://isdasoil.s3.amazonaws.com/catalog.json")

    for root, catalogs, items in catalog.walk():
        for item in items:
            for asset in item.assets.values():
                if asset.roles == ['data']:
                    # save all items to a dictionary as we go along
                    assets_dict[item.id] = item
    
    print('Populated iSDAsoil assets!')
    return assets_dict


def _get_url(id):
    url = st.session_state['ASSETS'][id].assets['image'].href
    print(url)
    return url


# @st.cache(allow_output_mutation=True)
def get_bbox_data(id, start_lat_lon, end_lat_lon, url=None, union=True):
    '''
    :param id: id of dataset
    :param start_lat_lon: upper left corner of the bounding box as lat, lon
    :param end_lat_lon: lower right corner of the bounding box as lat, lon
    :return: numpy array of the dataset, metadata required for writing back to tiff file
    '''

    if url:
        file_location = url
    else:
        file_location = _get_url(id)

    geo_json_lst = []

    with rio.open(file_location) as file:
        transformer = Transformer.from_crs("epsg:4326", file.crs)

        # convert the data from lat/lon to x,y coords of the source dataset crs
        start_coords = transformer.transform(start_lat_lon[0], start_lat_lon[1])
        end_coords = transformer.transform(end_lat_lon[0], end_lat_lon[1])
        # print('Bounds:', file.bounds)

        # get the location of the pixel at the given location (in lon/lat (x/y) order))
        start_coords= file.index(start_coords[0], start_coords[1])
        end_coords=file.index(end_coords[0], end_coords[1])

        window = rio.windows.Window(start_coords[1], start_coords[0], end_coords[1] - start_coords[1], end_coords[0] - start_coords[0])

        print('Getting data from file')
        arr = file.read(window=window)

        new_profile = file.profile.copy()

        # Get lon/lat
        transformer = Transformer.from_crs(file.crs, "epsg:4326")
        # grid_arr = np.zeros((arr.shape[1], arr.shape[2], 2))  # Last dim is 2 for lon/lat
        print('Populating GeoJSON')
        for x_idx in range(start_coords[0], end_coords[0]):
            inner_lst = []
            for y_idx in range(start_coords[1], end_coords[1]):
                # Create polygon
                polygon_coords = []
                for offset in ['ul', 'll', 'lr', 'ur']:
                    coords = file.xy(x_idx, y_idx, offset=offset)
                    coords = transformer.transform(*coords)
                    polygon_coords.append([coords[1], coords[0]])

                # Offset indexes by file's index
                x_idx_offsetted = x_idx - start_coords[0]
                y_idx_offsetted = y_idx - start_coords[1]
                xy_idx_offsetted = str(x_idx_offsetted) + '|' + str(y_idx_offsetted)

                polygon_dict = {
                    'coords': [polygon_coords],
                    'xy_idx_offsetted': xy_idx_offsetted,
                    'properties': {
                        'area_idxs': [[x_idx_offsetted, y_idx_offsetted]]
                    }
                }
                inner_lst.append(polygon_dict)
            geo_json_lst.append(inner_lst)
    
    new_profile.update({
        'height': window.height,
        'width': window.width,
        'count': file.count,
        'transform': file.window_transform(window)
    })

    arr = _back_transform(id, arr)

    geo_json = []

    if union:
        # Get shape
        x_lim, y_lim = arr.shape[1], arr.shape[2]
        accessed_dict = dict()
        for x_idx in range(0, x_lim):
            for y_idx in range(0, y_lim):
                datapoint = arr[0][x_idx][y_idx]
                frontier = [[x_idx, y_idx]]
                polygons_lst = []

                while len(frontier) > 0:
                    area_x, area_y = frontier.pop()

                    if not (area_x in accessed_dict and area_y in accessed_dict[area_x]) and \
                        (datapoint == arr[0][area_x][area_y]):
                        # Set accessed
                        accessed_dict[area_x] = accessed_dict.get(area_x, dict())
                        accessed_dict[area_x][area_y] = True
                        polygons_lst.append(geo_json_lst[area_x][area_y])

                        # Add surrounding areas to frontier
                        #   x, y  | x, y+1
                        #  x+1, y | 
                        # Down
                        neighbour_x = area_x + 1
                        neighbour_y = area_y

                        if neighbour_x >= 0 and \
                            neighbour_y >= 0 and \
                            neighbour_x < x_lim and \
                            neighbour_y < y_lim:
                            frontier.append([neighbour_x, neighbour_y])
                        # Right
                        neighbour_x = area_x
                        neighbour_y = area_y + 1

                        if neighbour_x >= 0 and \
                            neighbour_y >= 0 and \
                            neighbour_x < x_lim and \
                            neighbour_y < y_lim:
                            frontier.append([neighbour_x, neighbour_y])

                if len(polygons_lst) > 0:
                    # Merge polygons
                    feature = _merge_polygons(polygons_lst)
                    geo_json.append(feature)

    if not union:
        for inner_lst in geo_json_lst:
            for feature_dict in inner_lst:
                polygon = geojson.Polygon(feature_dict['coords'])
                feature = geojson.Feature(geometry=polygon, 
                                            id=feature_dict['xy_idx_offsetted'], 
                                            properties=feature_dict['properties'])
                geo_json.append(feature)
    
    geo_json = geojson.FeatureCollection(geo_json)

    return arr, geo_json, new_profile


# @st.cache(hash_funcs={geojson.feature.FeatureCollection: lambda _: None})
def get_point_geojson(id, lat_lon, vicinity_in_metres, data_arr=None, union=True, url=None):
    '''
    :param id: id of dataset
    :param start_lat_lon: upper left corner of the bounding box as lat, lon
    :param end_lat_lon: lower right corner of the bounding box as lat, lon
    :return: numpy array of the dataset, metadata required for writing back to tiff file
    '''

    if url:
        file_location = url
    else:
        file_location = _get_url(id)
    
    geo_json_lst = []

    with rio.open(file_location) as file:
        transformer = Transformer.from_crs("epsg:4326", file.crs)

        # convert the data from lat/lon to x,y coords of the source dataset crs
        coords = transformer.transform(lat_lon[0], lat_lon[1])

        # get the location of the pixel at the given location (in lon/lat (x/y) order))
        coords = file.index(coords[0], coords[1])
        offset = round(vicinity_in_metres / 30 / 2)  # Each block is 30m, divide 2 for top/bottom and left/right

        window = rio.windows.Window(coords[1] - offset, coords[0] - offset, offset * 2 + 1, offset * 2 + 1)

        if data_arr is None:
            print('Getting data from file')
            arr = file.read(window=window)
            arr = _back_transform(id, arr)
        else:
            arr = np.array([data_arr])

        # Get lon/lat
        transformer = Transformer.from_crs(file.crs, "epsg:4326")
        # grid_arr = np.zeros((arr.shape[1], arr.shape[2], 2))  # Last dim is 2 for lon/lat
        print('Populating GeoJSON')
        for x_idx in range(coords[0] - offset, coords[0] + offset + 1):
            inner_lst = []
            for y_idx in range(coords[1] - offset, coords[1] + offset + 1):
                # Create polygon
                polygon_coords = []
                for _offset in ['ul', 'll', 'lr', 'ur']:
                    _coords = file.xy(x_idx, y_idx, offset=_offset)
                    _coords = transformer.transform(*_coords)
                    polygon_coords.append([_coords[1], _coords[0]])

                # Offset indexes by file's index
                x_idx_offsetted = x_idx - coords[0] + offset
                y_idx_offsetted = y_idx - coords[1] + offset
                xy_idx_offsetted = str(x_idx_offsetted) + '|' + str(y_idx_offsetted)

                polygon_dict = {
                    'coords': [polygon_coords],
                    'xy_idx_offsetted': xy_idx_offsetted,
                    'properties': {
                        'area_idxs': [[x_idx_offsetted, y_idx_offsetted]]
                    }
                }
                inner_lst.append(polygon_dict)
            geo_json_lst.append(inner_lst)

    geo_json = []

    if union:
        # Get shape
        x_lim, y_lim = arr.shape[1], arr.shape[2]
        accessed_dict = dict()
        for x_idx in range(0, x_lim):
            for y_idx in range(0, y_lim):
                datapoint = arr[0][x_idx][y_idx]
                frontier = [[x_idx, y_idx]]
                polygons_lst = []

                while len(frontier) > 0:
                    area_x, area_y = frontier.pop()

                    if not (area_x in accessed_dict and area_y in accessed_dict[area_x]) and \
                        (datapoint == arr[0][area_x][area_y]):
                        # Set accessed
                        accessed_dict[area_x] = accessed_dict.get(area_x, dict())
                        accessed_dict[area_x][area_y] = True
                        polygons_lst.append(geo_json_lst[area_x][area_y])

                        # Add surrounding areas to frontier
                        #   x, y  | x, y+1
                        #  x+1, y | 
                        # Down
                        neighbour_x = area_x + 1
                        neighbour_y = area_y

                        if neighbour_x >= 0 and \
                            neighbour_y >= 0 and \
                            neighbour_x < x_lim and \
                            neighbour_y < y_lim:
                            frontier.append([neighbour_x, neighbour_y])
                        # Right
                        neighbour_x = area_x
                        neighbour_y = area_y + 1

                        if neighbour_x >= 0 and \
                            neighbour_y >= 0 and \
                            neighbour_x < x_lim and \
                            neighbour_y < y_lim:
                            frontier.append([neighbour_x, neighbour_y])

                if len(polygons_lst) > 0:
                    # Merge polygons
                    feature = _merge_polygons(polygons_lst)
                    geo_json.append(feature)

    if not union:
        for inner_lst in geo_json_lst:
            for feature_dict in inner_lst:
                polygon = geojson.Polygon(feature_dict['coords'])
                feature = geojson.Feature(geometry=polygon, 
                                            id=feature_dict['xy_idx_offsetted'], 
                                            properties=feature_dict['properties'])
                geo_json.append(feature)
    
    geo_json = geojson.FeatureCollection(geo_json)

    return geo_json


@st.cache(allow_output_mutation=True)
def get_point_data(id, lat_lon, vicinity_in_metres, url=None):
    '''
    :param id: id of dataset
    :param start_lat_lon: upper left corner of the bounding box as lat, lon
    :param end_lat_lon: lower right corner of the bounding box as lat, lon
    :return: numpy array of the dataset, metadata required for writing back to tiff file
    '''

    if url:
        file_location = url
    else:
        file_location = _get_url(id)

    with rio.open(file_location) as file:
        transformer = Transformer.from_crs("epsg:4326", file.crs)

        # convert the data from lat/lon to x,y coords of the source dataset crs
        coords = transformer.transform(lat_lon[0], lat_lon[1])

        # get the location of the pixel at the given location (in lon/lat (x/y) order))
        coords = file.index(coords[0], coords[1])
        offset = round(vicinity_in_metres / 30 / 2)  # Each block is 30m, divide 2 for top/bottom and left/right

        window = rio.windows.Window(coords[1] - offset, coords[0] - offset, offset * 2 + 1, offset * 2 + 1)

        print('Getting data from file')
        arr = file.read(window=window)
    
    arr = _back_transform(id, arr)

    return arr


def get_fcc_mapping():
    print('Retrieving FCC mapping')
    fcc_mapping_url = st.session_state['ASSETS']['fcc'].assets['metadata'].href
    fcc_mapping_df = pd.read_csv(fcc_mapping_url)
    
    fcc_mapping_mle_df = fcc_mapping_df['Description'].str.lower().str.get_dummies(', ')
    fcc_mapping_df = fcc_mapping_df.join(fcc_mapping_mle_df)
    
    fcc_mapping_df.columns = ['fcc_' + col.lower().strip().replace(' ', '_') for col in fcc_mapping_df.columns]
    return fcc_mapping_df


def _back_transform(id, data):
    print('Transforming data')
    conversion = st.session_state['ASSETS'][id].extra_fields['back-transformation']
    return CONVERSION_FUNCS_DICT[conversion](data)


def _merge_polygons(polygons_lst):

    if len(polygons_lst) == 0:
        return
    
    if len(polygons_lst) == 1:
        feature_dict = polygons_lst[0]
        polygon = geojson.Polygon(feature_dict['coords'])
        feature = geojson.Feature(geometry=polygon, 
                                    id=feature_dict['xy_idx_offsetted'], 
                                    properties=feature_dict['properties'])
        return feature

    # Convert to shapely polygons
    shapely_polygons_lst = []
    for feature_dict in polygons_lst:
        coords = feature_dict['coords']
        shapely_polygon = Polygon(coords[0])

        if len(coords) > 1:
            shapely_polygon = Polygon(coords[0], holes=coords[1])

        shapely_polygons_lst.append(shapely_polygon)

    # Merge polygons
    merged_polygon = unary_union(shapely_polygons_lst)

    # Convert back to GeoJSON Polygon Feature
    polygon_coords = [list(merged_polygon.exterior.coords)]
    
    for interior in merged_polygon.interiors:
        polygon_coords.append(list(interior.coords))
    
    polygon = geojson.Polygon(polygon_coords)
    _id = polygons_lst[0]['xy_idx_offsetted']
    area_idxs = []
    for feature_dict in polygons_lst:
        area_idxs = area_idxs + feature_dict['properties']['area_idxs']
    
    merged_geojson_polygon_feature = geojson.Feature(geometry=polygon, 
                                                     id=_id, 
                                                     properties={
                                                        'area_idxs': area_idxs
                                                     })

    return merged_geojson_polygon_feature
