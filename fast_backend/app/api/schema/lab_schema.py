from pydantic import BaseModel, Field


class Compound(BaseModel):
    name: str
    compound_class: str = Field(alias="class")
    marker_for: str
    pnec_ng_l: float

    model_config = {"populate_by_name": True}


class Campaign(BaseModel):
    id: str
    name: str
    season: str
    start: str
    end: str
    type: str                   # seasonal | event
    trigger: str | None = None
    samples: int


class Detection(BaseModel):
    compound: str
    compound_class: str
    marker_for: str
    concentration_ng_l: float
    pnec_ng_l: float
    risk_quotient: float        # concentration / PNEC
    screening: str              # target | suspect | non-target


class Sample(BaseModel):
    id: str
    campaign_id: str
    station_id: str
    site: str
    matrix: str                 # water | sediment | groundwater
    lat: float
    lon: float
    collected_at: str
    collector: str              # autosampler | boat | manual
    detections: list[Detection]


class SourceShare(BaseModel):
    source: str
    share_pct: float


class SourceApportionment(BaseModel):
    station_id: str
    site: str
    campaign_id: str
    sources: list[SourceShare]
