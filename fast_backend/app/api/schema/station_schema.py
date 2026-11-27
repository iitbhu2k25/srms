from pydantic import BaseModel


class Station(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    reach: str
    district: str
    chainage_km: float
    telemetry: str
    installed: str


class StationLatest(Station):
    status: str                 # good | moderate | poor | critical | offline
    health_index: float         # 0-100
    last_seen: str | None
    battery_v: float | None
    signal_dbm: float | None
    reading: dict[str, float]
    exceedances: list[str]      # parameter keys outside permissible limits


class SeriesPoint(BaseModel):
    t: str
    v: float | None


class ParameterSeries(BaseModel):
    station_id: str
    parameter: str
    label: str
    unit: str
    limit_min: float | None = None
    limit_max: float | None = None
    points: list[SeriesPoint]


class ForecastDay(BaseModel):
    date: str
    fecal_coliform_mpn: int     # MPN/100 mL
    category: str               # Safe | Caution | Unsafe
    confidence: float


class StationForecast(BaseModel):
    station_id: str
    model: str
    issued: str
    days: list[ForecastDay]


class Well(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    paired_station: str
    depth_m: float
    zone: str
    latest: dict[str, float]
    river_level_m: float | None
    head_difference_m: float | None   # +ve: aquifer feeds river (gaining)
    exchange: str                     # gaining | losing | disconnected | unknown


class WellSeries(BaseModel):
    well_id: str
    points: list[dict]
