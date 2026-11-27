# SMART-STREAM boat mission and waypoints (media/data/boat_mission.json).
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json  # noqa: E402

import pandas as pd  # noqa: E402
from db_connection import DATA_DIR, engine, table_has_rows  # noqa: E402

JSON_FILE = os.path.join(DATA_DIR, "boat_mission.json")


def load():
    try:
        if table_has_rows("boat_missions"):
            print("boat_missions already has data, skipping.")
            return
        m = json.load(open(JSON_FILE, encoding="utf-8"))
        pd.DataFrame([{k: m[k] for k in ("mission_code", "name", "vessel", "loop_minutes")} | {"is_active": True}]) \
            .to_sql("boat_missions", engine, if_exists="append", index=False)
        wps = pd.DataFrame(m["waypoints"]).assign(mission_code=m["mission_code"])
        wps["bottle"] = wps["bottle"].astype("Int64")
        wps.to_sql("boat_waypoints", engine, if_exists="append", index=False)
        print(f"Mission {m['mission_code']} with {len(wps)} waypoints inserted.")
    except Exception as e:
        print("An error occurred:", e)
        sys.exit(1)


if __name__ == "__main__":
    load()
