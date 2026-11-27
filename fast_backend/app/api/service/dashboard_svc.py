from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.service.alert_svc import alert_svc
from app.api.service.health_svc import health_svc
from app.api.service.station_svc import station_svc
from app.database.crud.lab.async_crud import Lab_crud
from app.database.crud.reading.async_crud import Reading_crud
from app.database.crud.station.async_crud import Station_crud
from app.database.crud.survey.async_crud import Survey_crud


class dashboard_svc:

    async def get_overview(db: AsyncSession) -> dict:
        latest = await station_svc.list_latest(db)
        online = [s for s in latest if s["status"] != "offline"]
        rhi_now = round(sum(s["health_index"] for s in latest) / len(latest), 1) if latest else 0.0
        past = await Reading_crud(db).at_time(datetime.now(timezone.utc) - timedelta(days=30))
        rhi_past = sum(health_svc.health_index(r) for r in past) / len(past) if past else rhi_now
        alerts = [a for a in await alert_svc.list_alerts(db, None, None, None) if a["status"] != "resolved"]
        lab = Lab_crud(db)
        campaign = await lab.latest_seasonal_campaign()
        last_seen = max((s["last_seen"] for s in latest if s["last_seen"]), default=None)
        return {
            "kpi": {
                "river_health_index": rhi_now,
                "rhi_category": health_svc.category(rhi_now),
                "rhi_change_30d": round(rhi_now - rhi_past, 1),
                "stations_online": len(online),
                "stations_total": len(latest),
                "active_alerts": len(alerts),
                "critical_alerts": sum(a["severity"] == "critical" for a in alerts),
                "samples_this_season": await lab.count_samples(campaign) if campaign else 0,
                "hotspots": await Survey_crud(db).count_hotspots(),
                "last_sync": last_seen or datetime.now(timezone.utc).isoformat(),
            },
            "river_line": await Station_crud(db).get_centerline(),
        }

    async def get_health_history(db: AsyncSession, months: int) -> list[dict]:
        now = datetime.now(timezone.utc)
        y, m = now.year, now.month - (months - 1)
        while m <= 0:
            m, y = m + 12, y - 1
        rows = await Reading_crud(db).monthly_means(datetime(y, m, 1, tzinfo=timezone.utc))
        by_month: dict[str, dict] = {}
        for r in rows:
            key = r["month"].strftime("%Y-%m")
            by_month.setdefault(key, {})[r["station_code"]] = health_svc.health_index(r)
        return [{"month": k, "rhi": round(sum(v.values()) / len(v), 1), "by_station": v} for k, v in sorted(by_month.items())]
