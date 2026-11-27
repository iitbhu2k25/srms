from sqlalchemy import Float, Numeric, cast, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud.base.async_base import CrudBase
from app.database.models import BasinBoundary, Drain, River, Stp

# Douglas–Peucker tolerance in degrees (~20 m / ~50 m): keeps map payloads small without visible loss.
RIVER_TOLERANCE = 0.0002
BOUNDARY_TOLERANCE = 0.0005


def _geojson(geom, tolerance: float | None = None):
    shape = func.ST_SimplifyPreserveTopology(geom, tolerance) if tolerance else geom
    return func.ST_AsGeoJSON(shape, 6)


def _geography(geom):
    return func.Geography(geom)


DRAIN_COLUMNS = [Drain.drain_code, Drain.name, Drain.river_name, Drain.river_code, Drain.tapping_status, Drain.discharge,
                 Drain.elevation_m, Drain.lat, Drain.lon]
STP_COLUMNS = [Stp.stp_code, Stp.name, Stp.status, Stp.maintained_by, Stp.stp_type, Stp.capacity_mld, Stp.utilized_mld,
               Stp.bod_actual, Stp.bod_design, Stp.cod_actual, Stp.cod_design, Stp.tss_actual, Stp.tss_design,
               Stp.ph_actual, Stp.ph_design, Stp.fc_actual, Stp.fc_design, Stp.remarks, Stp.tapped_drains,
               Stp.river_name, Stp.district, Stp.lat, Stp.lon]


class Spatial_crud(CrudBase):

    def __init__(self, db: AsyncSession, Model=River):
        super().__init__(db, Model)

    async def get_boundary(self) -> dict | None:
        query = select(BasinBoundary.name, _geojson(BasinBoundary.geom, BOUNDARY_TOLERANCE).label("geom"),
                       (func.ST_Area(_geography(BasinBoundary.geom)) / 1e6).label("area_km2")).limit(1)
        row = (await self.db.execute(query)).mappings().first()
        return dict(row) if row else None

    async def get_rivers(self) -> list[dict]:
        return await self._rows(select(River.river_code, River.name, River.length_km,
                                       _geojson(River.geom, RIVER_TOLERANCE).label("geom")).order_by(River.river_code))

    async def get_drains(self, river: str | None, tapping: str | None) -> list[dict]:
        query = select(*DRAIN_COLUMNS).order_by(Drain.river_code, Drain.drain_code)
        if river:
            query = query.where(func.lower(Drain.river_name) == river.lower())
        if tapping:
            query = query.where(func.lower(Drain.tapping_status) == tapping.lower())
        return await self._rows(query)

    async def drain_summary(self) -> list[dict]:
        q = Drain.discharge
        query = (select(Drain.river_name, func.count().label("drains"),
                        func.count().filter(Drain.tapping_status == "Tapped").label("tapped"),
                        func.count().filter(Drain.tapping_status == "Partial").label("partial"),
                        func.count().filter(Drain.tapping_status == "Untapped").label("untapped"),
                        func.count(q).label("with_discharge"),
                        func.round(func.coalesce(func.sum(q), 0).cast(Numeric), 1).label("discharge_total"),
                        func.round(func.coalesce(func.sum(q).filter(Drain.tapping_status != "Tapped"), 0).cast(Numeric), 1)
                        .label("discharge_untreated"))
                 .group_by(Drain.river_name).order_by(func.count().desc()))
        return await self._rows(query)

    async def get_stps(self) -> list[dict]:
        return await self._rows(select(*STP_COLUMNS, _geojson(Stp.geom).label("footprint")).order_by(Stp.stp_code))

    async def near_station(self, lat: float, lon: float, radius_m: float) -> dict:
        """Drains within radius_m of a point and the two nearest STPs, with their distance in metres."""
        point = _geography(func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326))
        d_drain = cast(func.ST_Distance(point, _geography(Drain.geom)), Float).label("distance_m")
        drains = await self._rows(select(*DRAIN_COLUMNS, d_drain)
                                  .where(func.ST_DWithin(point, _geography(Drain.geom), radius_m)).order_by(d_drain))
        d_stp = cast(func.ST_Distance(point, _geography(Stp.geom)), Float).label("distance_m")
        stps = await self._rows(select(Stp.stp_code, Stp.name, Stp.status, Stp.capacity_mld, Stp.utilized_mld, d_stp)
                                .order_by(d_stp).limit(2))
        return {"drains": drains, "nearest_stps": stps}

    async def river_path(self, river: str, start: tuple[float, float], end: tuple[float, float]) -> list[list[float]]:
        """[[lat, lon], ...] along the river between two (lat, lon) points, in travel order."""
        sql = text("""
            WITH part AS (
                SELECT d.geom FROM rivers r, ST_Dump(r.geom) d
                WHERE r.name = :river
                ORDER BY ST_Distance(d.geom, ST_SetSRID(ST_MakePoint(:lon1, :lat1), 4326)) LIMIT 1
            ), f AS (
                SELECT geom, ST_LineLocatePoint(geom, ST_SetSRID(ST_MakePoint(:lon1, :lat1), 4326)) a,
                             ST_LineLocatePoint(geom, ST_SetSRID(ST_MakePoint(:lon2, :lat2), 4326)) b FROM part
            )
            SELECT ST_AsGeoJSON(CASE WHEN a <= b THEN ST_LineSubstring(geom, a, b)
                                     ELSE ST_Reverse(ST_LineSubstring(geom, b, a)) END, 6) FROM f
        """)
        geojson = await self.db.scalar(sql, {"river": river, "lat1": start[0], "lon1": start[1], "lat2": end[0], "lon2": end[1]})
        if not geojson:
            return []
        import json
        return [[lat, lon] for lon, lat in json.loads(geojson)["coordinates"]]
