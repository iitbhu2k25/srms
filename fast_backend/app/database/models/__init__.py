from app.database.models.base import Base
from app.database.models.station import Station, Parameter
from app.database.models.reading import RiverReading, READING_COLUMNS
from app.database.models.groundwater import Well, WellReading
from app.database.models.boat import BoatMission, BoatWaypoint, BoatCommand
from app.database.models.lab import (
    Campaign,
    Compound,
    Sample,
    Detection,
    SourceApportionment,
)
from app.database.models.survey import (
    TemTransect,
    Survey,
    Hotspot,
    CrossSection,
)
from app.database.models.spatial import (
    BasinBoundary,
    River,
    Drain,
    Stp,
)
