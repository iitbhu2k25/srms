import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_connection import DATA_DIR, engine, table_has_rows  # noqa: E402

# IoT river monitoring stations (approximate coordinates)
TABLE_NAME = 'stations'
CSV_FILE = os.path.join(DATA_DIR, "stations.csv")


def load_csv_to_db():
    try:
        if table_has_rows(TABLE_NAME):
            print(f"{TABLE_NAME} already has data, skipping.")
            return
        # Read the CSV file
        df = pd.read_csv(CSV_FILE)
        df['installed'] = pd.to_datetime(df['installed']).dt.date
        df['is_active'] = df['is_active'].astype(bool)
        # Store data in the database
        df.to_sql(TABLE_NAME, engine, if_exists='append', index=False, method='multi', chunksize=5000)
        print(f"{len(df)} rows from {CSV_FILE} have been successfully inserted into {TABLE_NAME}.")

    except Exception as e:
        print("An error occurred:", e)
        sys.exit(1)


if __name__ == "__main__":
    load_csv_to_db()
