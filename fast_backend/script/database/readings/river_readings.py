# Seeds one year of 15-min IoT readings per station from the dummy model (app/api/service/simulator_svc/generator.py).
# Inactive stations stop OFFLINE_GAP before now, so the dashboard shows them "offline".
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import timedelta  # noqa: E402

import pandas as pd  # noqa: E402
from db_connection import DATA_DIR, copy_rows, engine, table_has_rows  # noqa: E402,F401

from app.api.service.simulator_svc import generator as g  # noqa: E402
from app.database.models import READING_COLUMNS  # noqa: E402

TABLE_NAME = 'river_readings'
HISTORY_DAYS = 365
OFFLINE_GAP = timedelta(hours=3, minutes=45)
COLUMNS = ["station_code", "ts", "source", *READING_COLUMNS, "battery_v", "signal_dbm"]


def rows():
    stations = pd.read_csv(os.path.join(DATA_DIR, "stations.csv"))
    end = g.floor_to_interval(g.now_utc())
    for s in stations.itertuples():
        stop = end if s.is_active else g.floor_to_interval(end - OFFLINE_GAP)
        for ts in g.timestamps(HISTORY_DAYS * 24, g.INTERVAL_MIN, stop):
            yield {"station_code": s.station_code, "ts": ts.isoformat(), "source": "simulator",
                   **g.river_reading(s.station_code, s.profile, ts)}


def load():
    try:
        if table_has_rows(TABLE_NAME):
            print(f"{TABLE_NAME} already has data, skipping.")
            return
        n = copy_rows(TABLE_NAME, COLUMNS, rows())
        print(f"{n} rows ({HISTORY_DAYS} days, {g.INTERVAL_MIN}-min) have been successfully inserted into {TABLE_NAME}.")
    except Exception as e:
        print("An error occurred:", e)
        sys.exit(1)


if __name__ == "__main__":
    load()
