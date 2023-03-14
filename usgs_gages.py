"""
usgs_gages.py
=============
Query the NWIS Site Service

TODO:
* More query parameters
    * startDt
    * endDt
    * period
    * modifiedSince
* Use Git
* Unit tests
* Proper type hints
* Proper docstrings
* Reimplement with open-source libraries

DONE:
* Add a '--site-status' option
"""

import arcpy
import requests
import numpy as np 
import pandas as pd

import argparse
from datetime import date
from enum import Enum
from io import StringIO
import os
from typing import Optional, Tuple


USGS_SITE_API_BASE_URL = 'https://waterservices.usgs.gov/nwis/site/'

# USGS site service's latitude / longitude column names
DEC_LAT_VA = 'dec_lat_va'
DEC_LONG_VA = 'dec_long_va'

PANDAS_ESRI_DTYPES = {
    np.dtype('O'): 'TEXT',
    np.dtype('float64'): 'DOUBLE',
}


class UsgsSiteStatus(Enum):
    ALL = 'all'
    ACTIVE = 'active'
    INACTIVE = 'inactive'


class UsgsSiteServiceRequest:
    lon_west: float
    lat_south: float
    lon_east: float
    lat_north: float
    site_status: UsgsSiteStatus = UsgsSiteStatus.ALL
    start_dt: Optional[date] = None
    end_dt: Optional[date] = None

    def __init__(self, lon_west: float, lat_south: float, lon_east: float, lat_north: float) -> None:
        self.lon_west = lon_west
        self.lat_south = lat_south
        self.lon_east = lon_east
        self.lat_north = lat_north

    def get(self) -> requests.Response:
        response = requests.get(USGS_SITE_API_BASE_URL, {
            'format': 'rdb',
            'bBox': f'{self.lon_west:.7f},{self.lat_south:.7f},{self.lon_east:.7f},{self.lat_north:.7f}',
            'siteStatus': self.site_status.value,
            'startDt': self.start_dt.isoformat() if self.start_dt else None,
            'endDt': self.end_dt.isoformat() if self.end_dt else None,
        })
        return response


def parse_sites(sites_data: str) -> pd.DataFrame:
    df: pd.DataFrame = pd.read_csv(StringIO(sites_data), sep='\t', comment='#', header=[0, 1],
                                   dtype={'site_no': str, 'huc_cd': str})
    df.columns = df.columns.droplevel(1)
    df.dropna(subset=[DEC_LAT_VA, DEC_LONG_VA], inplace=True)
    return df


def replace_nan(df: pd.DataFrame, nan_numeric=-9999, nan_str='') -> pd.DataFrame:
    numeric_cols = list(df.select_dtypes(include=[np.number]).columns.values)
    df[numeric_cols] = df[numeric_cols].replace(np.nan, nan_numeric)

    object_cols = list(df.select_dtypes(include=[object]).columns.values)
    df[object_cols] = df[object_cols].replace(np.nan, nan_str)

    return df


def get_df_esri_types(df: pd.DataFrame, truncate_col_names: bool = True) -> list:
    # [ 
    #     ('field1', 'TEXT'),
    #     ('field2', 'DOUBLE'),
    #     ('field3', 'DOUBLE'),
    #     ...
    # ] 
    col_names = [col[:10] if truncate_col_names else col for col in df.columns]
    col_types = [PANDAS_ESRI_DTYPES[t] for t in df.dtypes]
    return list(zip(col_names, col_types))


def create_feature_class(out_path: str, out_name: str, fields: list):
    arcpy.CreateFeatureclass_management(out_path, out_name, geometry_type='POINT', spatial_reference=arcpy.SpatialReference(4326))
    arcpy.AddFields_management(os.path.join(out_path, out_name), fields)


def write_feature_class(path: str, df: pd.DataFrame, fields: list, col_x: str, col_y: str):
    field_names = [f[0] for f in fields]
    with arcpy.da.InsertCursor(path, [*field_names, 'SHAPE@XY']) as ic:
        for _, df_row in df.iterrows():
            values = [df_row[col] for col in df.columns]
            point = (df_row[col_x], df_row[col_y])
            row = [*values, point]
            ic.insertRow(row)


def get_wgs84_extent(feature_class: str) -> Tuple[arcpy.Point, arcpy.Point]:
    """
    get the extent of a feature class in WGS 84 / 4326 coordinates
    """
    desc = arcpy.Describe(feature_class)
    lower_left = arcpy.PointGeometry(desc.Extent.lowerLeft, desc.Extent.spatialReference).projectAs(arcpy.SpatialReference(4326)).firstPoint
    upper_right = arcpy.PointGeometry(desc.Extent.upperRight, desc.Extent.spatialReference).projectAs(arcpy.SpatialReference(4326)).firstPoint
    return lower_left, upper_right


def main(extent: str, output: str, overwrite: bool, clip: bool, site_status: UsgsSiteStatus, start_dt: Optional[date], end_dt: Optional[date],
         period: Optional[str] = None, modified_since: Optional[date] = None):
    if clip:
        output_dirname = 'memory'
        output_basename = arcpy.ValidateTableName(os.path.splitext(os.path.basename(output))[0], output_dirname)
        output_tmp = os.path.join(output_dirname, output_basename)
    else:
        output_dirname = os.path.dirname(output)
        # output_basename = arcpy.ValidateTableName(os.path.basename(output), output_dirname)
        output_basename = os.path.basename(output)

    # get extent in WGS-84 coordinates
    lower_left, upper_right = get_wgs84_extent(extent)

    # get response from USGS gages API
    usgs_gages_request = UsgsSiteServiceRequest(lower_left.X, lower_left.Y, upper_right.X, upper_right.Y)
    usgs_gages_request.site_status = site_status
    usgs_gages_request.start_dt = start_dt
    usgs_gages_request.end_dt = end_dt
    usgs_gages_response = usgs_gages_request.get()

    # load response into DataFrame
    df = parse_sites(usgs_gages_response.text)

    # get mapping of DataFrame field names and ESRI field types
    fields = get_df_esri_types(df)

    if overwrite:
        arcpy.env.overwriteOutput = True

    # create an empty feature class for the gages
    create_feature_class(output_dirname, output_basename, fields)

    # if writing out to a shapefile, replace NaN values in the DataFrame.
    if extent.lower().endswith('.shp'):
        df = replace_nan(df)

    if clip:
        # write gages to a temporary feature class, then clip and write to output path 
        write_feature_class(output_tmp, df, fields, DEC_LONG_VA, DEC_LAT_VA)
        arcpy.Clip_analysis(output_tmp, extent, output)
    else:
        # write gages to output path
        write_feature_class(output, df, fields, DEC_LONG_VA, DEC_LAT_VA)


def get_usgs_gages(extent: str, output: str, overwrite: bool, clip: bool, site_status: UsgsSiteStatus):
    main(extent, output, overwrite, clip, site_status)


if __name__ == '__main__':
    '''
    > python usgs_gages.py extent.shp output.shp --clip --overwrite
    '''
    parser = argparse.ArgumentParser("usgs_gages.py", description="Grab USGS gages.")
    parser.add_argument('extent', type=str, help="Feature class representing area to query for USGS gages")
    parser.add_argument('output', type=str, help="New point feature class for storing USGS gage locations") 
    parser.add_argument('--clip', action='store_true', help="Clip output feature class to extent features" )
    parser.add_argument('--overwrite', action='store_true', help="Overwrite an existing output feature class")
    parser.add_argument('--site-status', choices=[s.value for s in UsgsSiteStatus], default=UsgsSiteStatus.ALL.value,
                        help="Query for gages with a specific site status")
    parser.add_argument('--start-dt', type=date.fromisoformat, help="Query for gages that collected data since this date")
    parser.add_argument('--end-dt', type=date.fromisoformat, help="Query for gages that collected data before this date")
    args = parser.parse_args()
    main(args.extent, args.output, args.overwrite, args.clip, UsgsSiteStatus(args.site_status), args.start_dt, args.end_dt)
