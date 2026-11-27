from pydantic import BaseModel


class Kpi(BaseModel):
    river_health_index: float
    rhi_category: str
    rhi_change_30d: float
    stations_online: int
    stations_total: int
    active_alerts: int
    critical_alerts: int
    samples_this_season: int
    hotspots: int
    untapped_drains: int            # Varuna drains not (fully) tapped
    untreated_discharge_mld: float  # surveyed discharge of those drains
    last_sync: str


class HealthHistoryPoint(BaseModel):
    month: str
    rhi: float
    by_station: dict[str, float]


class Overview(BaseModel):
    kpi: Kpi


class IngestReading(BaseModel):
    """Payload sent by an IoT station / ESP32 water-quality unit."""
    device_id: str
    timestamp: str | None = None
    lat: float | None = None
    lon: float | None = None
    readings: dict[str, float]


class IngestAck(BaseModel):
    accepted: bool
    device_id: str
    station_id: str
    timestamp: str
    stored: int
    flags: list[str]
