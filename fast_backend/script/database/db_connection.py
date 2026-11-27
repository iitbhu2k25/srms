import csv
import io
import os
import sys

from sqlalchemy import create_engine, text

# fast_backend/ (this file is fast_backend/script/database/db_connection.py): makes the backend package (app.*)
# importable when a loader is run directly.
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

# Database connection details (from the environment, same variables as docker-compose / .fastdb.env)
DB_USER = os.getenv("POSTGRES_USER", "srms")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "srms")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5433")
DB_NAME = os.getenv("POSTGRES_DB", "srms")

# The source (seed) data: loaders only read from media/ and write to the database.
MEDIA_DIR = os.path.join(BACKEND_DIR, "media")
DATA_DIR = os.path.join(MEDIA_DIR, "data")

# Create the database engine
engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")


def table_has_rows(table_name):
    """Loaders only fill empty tables, so re-running them is safe."""
    with engine.connect() as connection:
        return connection.execute(text(f"SELECT EXISTS (SELECT 1 FROM {table_name})")).scalar()


def copy_rows(table_name: str, columns: list[str], rows) -> int:
    """Bulk insert with PostgreSQL COPY (fast path for large generated time series)."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    n = 0
    for r in rows:
        writer.writerow(["" if r.get(c) is None else r[c] for c in columns])
        n += 1
    buf.seek(0)
    raw = engine.raw_connection()
    try:
        with raw.cursor() as cur:
            cols = ", ".join(f'"{c}"' for c in columns)  # quoted: "do" is a reserved word
            cur.copy_expert(f"COPY {table_name} ({cols}) FROM STDIN WITH (FORMAT csv, NULL '')", buf)
        raw.commit()
    finally:
        raw.close()
    return n
