# Varuna basin outline (media/Boundary/Boundary.shp, WGS84).
import os
import sys

import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiLineString, MultiPolygon
import shapely

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_connection import MEDIA_DIR, engine, table_has_rows  # noqa: E402


def to_2d(geom):
    """Drop Z values (the river shapefile is 3-D)."""
    return shapely.force_2d(geom)


TABLE_NAME = 'basin_boundary'
SHP_FILE = os.path.join(MEDIA_DIR, "Boundary", "Boundary.shp")


def load():
    try:
        if table_has_rows(TABLE_NAME):
            print(f"{TABLE_NAME} already has data, skipping.")
            return
        gdf = gpd.read_file(SHP_FILE).to_crs(4326)
        geom = gdf.geometry.apply(to_2d).union_all()
        geom = MultiPolygon([geom]) if geom.geom_type == "Polygon" else geom
        out = gpd.GeoDataFrame({"name": ["Varuna Basin"]}, geometry=[geom], crs=4326).rename_geometry("geom")
        out.to_postgis(TABLE_NAME, engine, if_exists='append', index=False)
        area = gpd.GeoSeries([geom], crs=4326).to_crs(32644).area.iloc[0] / 1e6
        print(f"Basin boundary ({area:,.0f} km²) from {SHP_FILE} inserted into {TABLE_NAME}.")
    except Exception as e:
        print("An error occurred:", e)
        sys.exit(1)


if __name__ == "__main__":
    load()
