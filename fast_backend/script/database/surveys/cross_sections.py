# Pre- vs post-monsoon bathymetric cross-sections in the urban reach (dummy echo-sounder output).
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import math  # noqa: E402

import pandas as pd  # noqa: E402
from db_connection import DATA_DIR, engine, table_has_rows  # noqa: E402
from sqlalchemy.dialects.postgresql import JSONB  # noqa: E402

from app.api.service.simulator_svc.generator import rng  # noqa: E402

TABLE_NAME = "cross_sections"
URBAN_FROM_KM = 160


def section(code: str):
    r = rng("xs", code)
    width, depth = 46 + r.random() * 18, 2.6 + r.random() * 1.4
    offs = [round(-width / 2 - 6 + i * 2, 1) for i in range(int((width + 12) / 2) + 1)]
    dep = (r.random() - 0.35) * 0.9  # +ve: net deposition
    pre, post = [], []
    for x in offs:
        u = min(1.0, abs(x) / (width / 2))
        bed = -depth * (1 - u ** 2.2) if abs(x) <= width / 2 else 0.4 * (abs(x) - width / 2) / 6
        bump = dep * (1 - u ** 2) + (0.25 * math.sin(x / 4) * r.random() if abs(x) < width / 2 else 0)
        pre.append(round(bed, 2))
        post.append(round(bed + bump, 2))
    return offs, pre, post, round(sum((b - a) * 2 for a, b in zip(pre, post)), 1)


def load():
    try:
        if table_has_rows(TABLE_NAME):
            print(f"{TABLE_NAME} already has data, skipping.")
            return
        stations = pd.read_csv(os.path.join(DATA_DIR, "stations.csv"))
        rows = []
        for s in stations[stations.chainage_km >= URBAN_FROM_KM].itertuples():
            offs, pre, post, change = section(s.station_code)
            rows.append({"station_code": s.station_code, "chainage_km": s.chainage_km, "location": s.name,
                         "offsets_m": offs, "pre_monsoon_bed_m": pre, "post_monsoon_bed_m": post, "net_change_m2": change})
        pd.DataFrame(rows).to_sql(TABLE_NAME, engine, if_exists="append", index=False,
                                  dtype={k: JSONB for k in ("offsets_m", "pre_monsoon_bed_m", "post_monsoon_bed_m")})
        print(f"{len(rows)} rows have been successfully inserted into {TABLE_NAME}.")
    except Exception as e:
        print("An error occurred:", e)
        sys.exit(1)


if __name__ == "__main__":
    load()
