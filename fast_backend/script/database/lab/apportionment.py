# Source apportionment per site and campaign (dummy PMF output driven by each site's pollution profile).
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd  # noqa: E402
from db_connection import DATA_DIR, engine, table_has_rows  # noqa: E402

from app.api.service.simulator_svc.generator import rng  # noqa: E402

TABLE_NAME = "source_apportionment"
BASE = {
    "clean":    {"Domestic sewage": 8, "Agricultural runoff": 62, "Industrial effluent": 4, "Urban stormwater": 6, "Hospital waste": 1, "Natural / background": 19},
    "moderate": {"Domestic sewage": 34, "Agricultural runoff": 38, "Industrial effluent": 9, "Urban stormwater": 10, "Hospital waste": 3, "Natural / background": 6},
    "poor":     {"Domestic sewage": 52, "Agricultural runoff": 12, "Industrial effluent": 15, "Urban stormwater": 13, "Hospital waste": 6, "Natural / background": 2},
    "severe":   {"Domestic sewage": 61, "Agricultural runoff": 5, "Industrial effluent": 17, "Urban stormwater": 9, "Hospital waste": 7, "Natural / background": 1},
}
EVENT_SITES = ("VR-04", "VR-05", "VR-06")


def load():
    try:
        if table_has_rows(TABLE_NAME):
            print(f"{TABLE_NAME} already has data, skipping.")
            return
        stations = pd.read_csv(os.path.join(DATA_DIR, "stations.csv"))
        campaigns = pd.read_csv(os.path.join(DATA_DIR, "campaigns.csv"))
        out = []
        for c in campaigns.itertuples():
            sites = stations[stations.station_code.isin(EVENT_SITES)] if c.campaign_type == "event" else stations
            for s in sites.itertuples():
                r = rng("pmf", c.campaign_code, s.station_code)
                raw = {k: max(0.5, v * (0.8 + 0.4 * r.random())) for k, v in BASE[s.profile].items()}
                tot = sum(raw.values())
                out += [{"campaign_code": c.campaign_code, "station_code": s.station_code, "source": k,
                         "share_pct": round(v / tot * 100, 1)} for k, v in raw.items()]
        pd.DataFrame(out).to_sql(TABLE_NAME, engine, if_exists="append", index=False, method="multi")
        print(f"{len(out)} rows have been successfully inserted into {TABLE_NAME}.")
    except Exception as e:
        print("An error occurred:", e)
        sys.exit(1)


if __name__ == "__main__":
    load()
