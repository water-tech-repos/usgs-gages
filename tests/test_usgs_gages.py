import pandas as pd
import pytest
import usgs_gages


def test_get_wgs84_extent():
    # test that the lower left and upper right corners of the extent are returned
    # in WGS-84 coordinates
    extent = 'tests/data/gages-extent.shp'
    lower_left, upper_right = usgs_gages.get_wgs84_extent(extent)
    assert lower_left.X == pytest.approx(-78.193949, abs=0.015)
    assert lower_left.Y == pytest.approx(37.008687, abs=0.015)
    assert upper_right.X == pytest.approx(-76.737630, abs=0.015)
    assert upper_right.Y == pytest.approx(37.882912, abs=0.015)


def test_get_df_esri_types():
    df = pd.DataFrame({
        'site_no': ['01646500', '01646500', '01646500'],
        'station_nm': ['JAMES RIVER AT CARTERSVILLE, VA', 'JAMES RIVER AT CARTERSVILLE, VA', 'JAMES RIVER AT CARTERSVILLE, VA'],
        'dec_lat_va': [37.6547222, 37.6547222, 37.6547222],
        'dec_long_va': [-78.16277778, -78.16277778, -78.16277778],
        'int_col1': [0, 1, 2],
        'int_col2': [0, 1, 2],
    })
    col_types = usgs_gages.get_df_esri_types(df, truncate_col_names=True)
    assert col_types == [
        ('site_no', 'TEXT'),
        ('station_nm', 'TEXT'),
        ('dec_lat_va', 'DOUBLE'),
        ('dec_long_v', 'DOUBLE'),
        ('int_col1', 'LONG'),
        ('int_col2', 'LONG'),
    ]
    col_types = usgs_gages.get_df_esri_types(df, truncate_col_names=False)
    assert col_types == [
        ('site_no', 'TEXT'),
        ('station_nm', 'TEXT'),
        ('dec_lat_va', 'DOUBLE'),
        ('dec_long_va', 'DOUBLE'),
        ('int_col1', 'LONG'),
        ('int_col2', 'LONG'),
    ]