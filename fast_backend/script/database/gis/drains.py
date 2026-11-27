# Drain outfalls (media/Drains/Drain.shp). -999 means "not surveyed" in the source and is stored as NULL.
import os
import sys

import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiLineString, MultiPolygon
from shapely.ops import transform

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_connection import MEDIA_DIR, engine, table_has_rows  # noqa: E402


def to_2d(geom):
    """Drop Z values (the river shapefile is 3-D)."""
    return transform(lambda x, y, z=None: (x, y), geom)


TABLE_NAME = 'drains'
SHP_FILE = os.path.join(MEDIA_DIR, "Drains", "Drain.shp")
MISSING = -999


def load():
    try:
        if table_has_rows(TABLE_NAME):
            print(f"{TABLE_NAME} already has data, skipping.")
            return
        gdf = gpd.read_file(SHP_FILE).to_crs(4326)
        gdf["geometry"] = gdf.geometry.apply(to_2d)
        out = gpd.GeoDataFrame({
            "drain_code": gdf["Drain_code"].astype(int),
            "name": gdf["Name"].str.strip().replace({"Unknown": None, "": None}),
            "river_name": gdf["River_name"].str.strip().str.title(),
            "river_code": gdf["river_code"].astype(int),
            "tapping_status": gdf["Tapping_st"].str.strip().str.title(),
            "discharge": gdf["Discharge"].where(gdf["Discharge"] > MISSING),
            "elevation_m": gdf["Elevation"].where(gdf["Elevation"] > MISSING),
            "lat": gdf.geometry.y.round(6),
            "lon": gdf.geometry.x.round(6),
        }, geometry=gdf.geometry.values, crs=4326).rename_geometry("geom")
        out.to_postgis(TABLE_NAME, engine, if_exists='append', index=False)
        counts = out.groupby("river_name").size().sort_values(ascending=False)
        print(f"{len(out)} drains ({', '.join(f'{k} {v}' for k, v in counts.items())}) inserted into {TABLE_NAME}.")
    except Exception as e:
        print("An error occurred:", e)
        sys.exit(1)


if __name__ == "__main__":
    load()
