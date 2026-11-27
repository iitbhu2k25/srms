from typing import Any

from pydantic import BaseModel


class GeoFeature(BaseModel):
    type: str = "Feature"
    geometry: dict[str, Any]
    properties: dict[str, Any]


class FeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[GeoFeature]


class DrainRecord(BaseModel):
    drain_code: int
    name: str | None
    river_name: str
    river_code: int
    tapping_status: str
    discharge: float | None
    elevation_m: float | None
    lat: float
    lon: float


class DrainNear(DrainRecord):
    distance_m: float


class DrainSummary(BaseModel):
    river_name: str
    drains: int
    tapped: int
    partial: int
    untapped: int
    with_discharge: int
    discharge_total: float
    discharge_untreated: float      # partial + untapped drains with a surveyed discharge


class StpRecord(BaseModel):
    stp_code: int
    name: str
    status: str | None
    maintained_by: str | None
    stp_type: str | None
    capacity_mld: float | None
    utilized_mld: float | None
    utilization_pct: float | None
    overloaded: bool
    bod_actual: float | None
    bod_design: float | None
    cod_actual: float | None
    cod_design: float | None
    tss_actual: float | None
    tss_design: float | None
    ph_actual: float | None
    ph_design: float | None
    fc_actual: float | None
    fc_design: float | None
    exceedances: list[str]          # parameters whose actual exceeds the design value
    remarks: str | None
    tapped_drains: list[int]
    river_name: str | None
    district: str | None
    lat: float
    lon: float
    footprint: dict[str, Any]


class StpNear(BaseModel):
    stp_code: int
    name: str
    status: str | None
    capacity_mld: float | None
    utilized_mld: float | None
    distance_m: float


class NearbySources(BaseModel):
    station_id: str
    radius_m: float
    drains: list[DrainNear]
    untapped: int
    discharge_untreated: float
    nearest_stps: list[StpNear]
