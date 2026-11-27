# Varuna main stem and tributaries (media/Rivers/Rivers.shp): one MultiLineString per river, Z dropped.
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


TABLE_NAME = 'rivers'
SHP_FILE = os.path.join(MEDIA_DIR, "Rivers", "Rivers.shp")


def load():
    try:
        if table_has_rows(TABLE_NAME):
            print(f"{TABLE_NAME} already has data, skipping.")
            return
        gdf = gpd.read_file(SHP_FILE).to_crs(4326)
        gdf["geometry"] = gdf.geometry.apply(to_2d)
        gdf = gdf.dissolve(by="River_Code", aggfunc={"name": "first"}).reset_index()
        gdf["geometry"] = gdf.geometry.apply(lambda g: MultiLineString([g]) if g.geom_type == "LineString" else g)
        gdf["length_km"] = (gdf.to_crs(32644).length / 1000).round(1)          # UTM 44N
        gdf = gdf.rename(columns={"River_Code": "river_code"})
        gdf["name"] = gdf["name"].str.strip().str.title()
        gdf = gdf[["river_code", "name", "length_km", "geometry"]].rename_geometry("geom")
        gdf.to_postgis(TABLE_NAME, engine, if_exists='append', index=False)
        summary = ", ".join(f"{r.name} {r.length_km} km" for r in gdf.itertuples())
        print(f"{len(gdf)} rivers ({summary}) inserted into {TABLE_NAME}.")
    except Exception as e:
        print("An error occurred:", e)
        sys.exit(1)


if __name__ == "__main__":
    load()
