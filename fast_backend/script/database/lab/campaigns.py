import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_connection import DATA_DIR, engine, table_has_rows  # noqa: E402

# Seasonal and event-triggered LC-HRMS sampling campaigns
TABLE_NAME = 'campaigns'
CSV_FILE = os.path.join(DATA_DIR, "campaigns.csv")


def load_csv_to_db():
    try:
        if table_has_rows(TABLE_NAME):
            print(f"{TABLE_NAME} already has data, skipping.")
            return
        # Read the CSV file
        df = pd.read_csv(CSV_FILE)
        df['start_date'] = pd.to_datetime(df['start_date']).dt.date
        df['end_date'] = pd.to_datetime(df['end_date']).dt.date
        df['trigger'] = df['trigger'].where(df['trigger'].notna(), None)
        # Store data in the database
        df.to_sql(TABLE_NAME, engine, if_exists='append', index=False, method='multi', chunksize=5000)
        print(f"{len(df)} rows from {CSV_FILE} have been successfully inserted into {TABLE_NAME}.")

    except Exception as e:
        print("An error occurred:", e)
        sys.exit(1)


if __name__ == "__main__":
    load_csv_to_db()
