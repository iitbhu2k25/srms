# Loads the GIS layers (media/*/*.shp) and the seed data (media/data) into the database by running the loaders in script/database/ in order.
# Each loader only fills an empty table, so this is safe to run on every start.
# Usage (from fast_backend/): python -m script.load_database
import os
import subprocess
import sys

base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database")


def run_scripts_in_sequence(script_list):
    """Runs the Python scripts in order, stopping at the first failure (later tables depend on earlier ones)."""
    for script in script_list:
        path = os.path.join(base_dir, script)
        if not os.path.exists(path):
            print(f"Error: Script {script} not found")
            sys.exit(1)

        print(f"Executing: {script}", flush=True)
        result = subprocess.run([sys.executable, path], capture_output=True, text=True)
        if result.stdout:
            print(result.stdout.strip(), flush=True)
        if result.stderr:
            print(result.stderr.strip(), flush=True)
        if result.returncode != 0:
            print(f"Script {script} failed with return code {result.returncode}")
            sys.exit(result.returncode)


if __name__ == "__main__":

    scripts_to_run = [
        # Reference data
        "masters/parameters.py",
        "masters/compounds.py",
        # GIS layers (media/Boundary, Rivers, Drains, STP shapefiles)
        "gis/basin_boundary.py",
        "gis/rivers.py",
        "gis/drains.py",
        "gis/stps.py",
        # Monitoring network (media/data)
        "stations/stations.py",
        "stations/wells.py",
        # Time series: one year of dummy history (a few seconds)
        "readings/river_readings.py",
        "readings/well_readings.py",
        # SMART-STREAM boat
        "boat/missions.py",
        # LC-HRMS fingerprinting
        "lab/campaigns.py",
        "lab/samples.py",
        "lab/apportionment.py",
        # TEM and drone / boat surveys
        "surveys/tem_transects.py",
        "surveys/surveys.py",
        "surveys/hotspots.py",
        "surveys/cross_sections.py",
    ]

    run_scripts_in_sequence(scripts_to_run)
