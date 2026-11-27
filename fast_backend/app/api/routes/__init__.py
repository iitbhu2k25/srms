from fastapi import APIRouter

from app.api.routes import alerts, boat, dashboard, drone, groundwater, ingest, lab, stations, tem

app_router = APIRouter()

app_router.include_router(
    dashboard.router,
    tags=["Dashboard"]
)
app_router.include_router(
    stations.router,
    prefix="/stations",
    tags=["IoT Stations"]
)
app_router.include_router(
    groundwater.router,
    prefix="/groundwater",
    tags=["Groundwater"]
)
app_router.include_router(
    alerts.router,
    prefix="/alerts",
    tags=["Alerts"]
)
app_router.include_router(
    boat.router,
    prefix="/boat",
    tags=["SMART-STREAM Boat"]
)
app_router.include_router(
    lab.router,
    prefix="/lab",
    tags=["LC-HRMS Fingerprinting"]
)
app_router.include_router(
    tem.router,
    prefix="/tem",
    tags=["TEM Geophysics"]
)
app_router.include_router(
    drone.router,
    prefix="/surveys",
    tags=["Drone & Boat Surveys"]
)
app_router.include_router(
    ingest.router,
    prefix="/ingest",
    tags=["Data Ingestion"]
)
