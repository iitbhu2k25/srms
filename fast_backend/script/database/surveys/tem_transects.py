# TEM transects with a synthetic 2-D resistivity section (stand-in for stitched 1-D inversions of real soundings).
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import math  # noqa: E402

import pandas as pd  # noqa: E402
from db_connection import DATA_DIR, engine, table_has_rows  # noqa: E402
from sqlalchemy.dialects.postgresql import JSONB  # noqa: E402

from app.api.service.simulator_svc.generator import rng  # noqa: E402

TABLE_NAME = "tem_transects"
CSV_FILE = os.path.join(DATA_DIR, "tem_transects.csv")


def resistivity(tid: str, x: float, z: float, length: float) -> float:
    """Resistivity (ohm-m) at distance x, depth z for an alluvial section with one feature per transect."""
    if z < 4:
        rho = 35          # topsoil
    elif z < 14:
        rho = 14          # clay / silt
    elif z < 60:
        rho = 85          # sandy aquifer
    elif z < 80:
        rho = 22          # deeper clay
    else:
        rho = 60          # older alluvium
    if tid == "TEM-T1" and math.hypot((x - length * 0.75) / 140, (z - 32) / 14) < 1:
        rho = 210         # buried paleo-channel
    elif tid == "TEM-T2" and 4 <= z < 26:
        rho = 9           # thick clay cap disconnecting river and aquifer
    elif tid == "TEM-T3":
        if math.hypot((x - length * 0.35) / 160, (z - 14) / 11) < 1:
            rho = 5       # contaminant plume core
        elif math.hypot((x - length * 0.35) / 230, (z - 16) / 16) < 1:
            rho = min(rho, 11)
    if abs(x - length * 0.5) < 40 and z < 6:
        rho = 18          # saturated sediment below the river bed
    return round(rho * (0.88 + 0.24 * rng("tem", tid, int(x), int(z)).random()), 1)


def interpretation(tid: str, length: float) -> list[dict]:
    return {
        "TEM-T1": [{"label": "Paleo-channel (sand)", "x_from": length * 0.6, "x_to": length * 0.9, "z_from": 18, "z_to": 46, "kind": "paleo"},
                   {"label": "Main aquifer", "x_from": 0, "x_to": length, "z_from": 14, "z_to": 60, "kind": "aquifer"}],
        "TEM-T2": [{"label": "Clay cap (aquitard)", "x_from": 0, "x_to": length, "z_from": 4, "z_to": 26, "kind": "clay"}],
        "TEM-T3": [{"label": "Contaminant plume", "x_from": length * 0.2, "x_to": length * 0.5, "z_from": 5, "z_to": 30, "kind": "plume"}],
    }.get(tid, [])


def load():
    try:
        if table_has_rows(TABLE_NAME):
            print(f"{TABLE_NAME} already has data, skipping.")
            return
        df = pd.read_csv(CSV_FILE)
        df["survey_date"] = pd.to_datetime(df["survey_date"]).dt.date
        sections = []
        for t in df.itertuples():
            xs = list(range(0, int(t.length_m) + 1, int(t.length_m / 30)))
            zs = list(range(0, 122, 4))
            sections.append({"distances_m": xs, "depths_m": zs,
                             "resistivity": [[resistivity(t.transect_code, x, z, t.length_m) for x in xs] for z in zs],
                             "interpretation": interpretation(t.transect_code, t.length_m)})
        df = pd.concat([df, pd.DataFrame(sections)], axis=1)
        df.to_sql(TABLE_NAME, engine, if_exists="append", index=False,
                  dtype={k: JSONB for k in ("distances_m", "depths_m", "resistivity", "interpretation")})
        print(f"{len(df)} transects with resistivity sections inserted into {TABLE_NAME}.")
    except Exception as e:
        print("An error occurred:", e)
        sys.exit(1)


if __name__ == "__main__":
    load()
