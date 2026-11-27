# LC-HRMS samples and compound detections (dummy concentrations scaled by each site's pollution profile).
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, timedelta, timezone  # noqa: E402

import pandas as pd  # noqa: E402
from db_connection import DATA_DIR, engine, table_has_rows  # noqa: E402

from app.api.service.simulator_svc.generator import rng  # noqa: E402

# typical concentration (ng/L) at a "moderate" site
TYPICAL = {
    "Caffeine": 900, "Carbamazepine": 180, "Diclofenac": 120, "Sulfamethoxazole": 140, "Atrazine": 160,
    "Imidacloprid": 45, "PFOS": 3.5, "PFOA": 6, "Bisphenol A": 210, "17β-Estradiol": 1.2, "Triclosan": 35,
}
# multiplier per site profile, by marker family
FACTOR = {
    "clean":    {"Sewage": 0.08, "Agriculture": 0.9, "Industrial": 0.1, "Hospital": 0.05},
    "moderate": {"Sewage": 1.0, "Agriculture": 1.4, "Industrial": 0.6, "Hospital": 0.7},
    "poor":     {"Sewage": 4.5, "Agriculture": 0.8, "Industrial": 1.8, "Hospital": 2.5},
    "severe":   {"Sewage": 11.0, "Agriculture": 0.6, "Industrial": 3.2, "Hospital": 5.0},
}
MATRIX_FACTOR = {"water": 1.0, "sediment": 2.4, "groundwater": 0.18}
SUSPECT = {"PFOS", "17β-Estradiol"}  # identified by suspect screening (no in-house standard)
EVENT_SITES = ("VR-04", "VR-05", "VR-06")


def family(marker: str) -> str:
    for fam in ("Hospital", "Agriculture", "Industrial", "Sewage"):
        if fam.lower() in marker.lower():
            return fam
    return "Sewage"


def sites_for(campaign, stations, wells):
    river = stations[stations.station_code.isin(EVENT_SITES)] if campaign.campaign_type == "event" else stations
    out = [(s.station_code, s.name, s.lat, s.lon, s.profile, "water", "autosampler") for s in river.itertuples()]
    vr05 = stations[stations.station_code == "VR-05"].iloc[0]
    out.append((vr05.station_code, vr05["name"], vr05.lat, vr05.lon, vr05.profile, "sediment", "boat"))
    gw = wells[wells.well_code == "GW-03"].iloc[0]
    out.append((vr05.station_code, gw["name"], gw.lat, gw.lon, vr05.profile, "groundwater", "manual"))
    return out


def load():
    try:
        if table_has_rows("samples"):
            print("samples already has data, skipping.")
            return
        stations = pd.read_csv(os.path.join(DATA_DIR, "stations.csv"))
        wells = pd.read_csv(os.path.join(DATA_DIR, "wells.csv"))
        campaigns = pd.read_csv(os.path.join(DATA_DIR, "campaigns.csv"))
        compounds = pd.read_csv(os.path.join(DATA_DIR, "compounds.csv"))
        samples, detections = [], []
        for c in campaigns.itertuples():
            start = datetime.fromisoformat(c.start_date).replace(tzinfo=timezone.utc)
            for i, (code, site, lat, lon, profile, matrix, collector) in enumerate(sites_for(c, stations, wells)):
                sid = f"{c.campaign_code}-{code}-{matrix[:2].upper()}"
                samples.append({"sample_code": sid, "campaign_code": c.campaign_code, "station_code": code, "site": site,
                                "matrix": matrix, "lat": lat, "lon": lon, "collector": collector,
                                "collected_at": start + timedelta(hours=9 + i * 3)})
                r = rng("lc", sid)
                for comp in compounds.itertuples():
                    conc = TYPICAL[comp.name] * FACTOR[profile][family(comp.marker_for)] * MATRIX_FACTOR[matrix] * (0.6 + 0.8 * r.random())
                    if conc < 0.5 and r.random() < 0.6:
                        continue  # below detection limit
                    detections.append({"sample_code": sid, "compound": comp.name,
                                       "concentration_ng_l": round(conc, 2 if conc < 10 else 1),
                                       "screening": "suspect" if comp.name in SUSPECT else "target"})
        pd.DataFrame(samples).to_sql("samples", engine, if_exists="append", index=False)
        pd.DataFrame(detections).to_sql("detections", engine, if_exists="append", index=False, method="multi", chunksize=2000)
        print(f"{len(samples)} samples and {len(detections)} detections inserted.")
    except Exception as e:
        print("An error occurred:", e)
        sys.exit(1)


if __name__ == "__main__":
    load()
