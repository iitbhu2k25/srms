from pydantic import BaseModel


class TemTransect(BaseModel):
    id: str
    name: str
    survey_date: str
    length_m: float
    start: list[float]
    end: list[float]
    station: str
    finding: str


class TemSection(BaseModel):
    transect_id: str
    distances_m: list[float]
    depths_m: list[float]
    resistivity: list[list[float]]   # [depth][distance] in ohm-m
    interpretation: list[dict]


class Survey(BaseModel):
    id: str
    name: str
    date: str
    season: str
    platform: str
    area_km2: float
    gsd_cm: float


class Hotspot(BaseModel):
    id: str
    type: str
    lat: float
    lon: float
    survey: str
    detail: str
    severity: str


class CrossSection(BaseModel):
    chainage_km: float
    location: str
    offsets_m: list[float]
    pre_monsoon_bed_m: list[float]
    post_monsoon_bed_m: list[float]
    net_change_m2: float        # +ve deposition, -ve scour
