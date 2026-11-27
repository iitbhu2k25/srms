# Seeds one year of hourly groundwater-logger readings from the dummy model.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd  # noqa: E402
from db_connection import DATA_DIR, copy_rows, table_has_rows  # noqa: E402

from app.api.service.simulator_svc import generator as g  # noqa: E402

TABLE_NAME = 'well_readings'
HISTORY_DAYS = 365
COLUMNS = ["well_code", "ts", "depth_to_water_m", "ec", "temperature"]


def rows():
    wells = pd.read_csv(os.path.join(DATA_DIR, "wells.csv"))
    end = g.now_utc().replace(minute=0, second=0, microsecond=0)
    for w in wells.itertuples():
        for ts in g.timestamps(HISTORY_DAYS * 24, 60, end):
            yield {"well_code": w.well_code, "ts": ts.isoformat(), **g.well_reading(w.well_code, ts)}


def load():
    try:
        if table_has_rows(TABLE_NAME):
            print(f"{TABLE_NAME} already has data, skipping.")
            return
        n = copy_rows(TABLE_NAME, COLUMNS, rows())
        print(f"{n} rows have been successfully inserted into {TABLE_NAME}.")
    except Exception as e:
        print("An error occurred:", e)
        sys.exit(1)


if __name__ == "__main__":
    load()
