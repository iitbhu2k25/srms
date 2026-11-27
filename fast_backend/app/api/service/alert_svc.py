"""
Threshold alerts evaluated on the stored IoT readings.

Rules run on the on-the-hour readings of the last 48 h: an alert opens when a rule starts failing and resolves
when it passes again. Critical alerts set `sampling_triggered` (event-based LC-HRMS sampling).
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.service.simulator_svc.generator import rng
from app.conf.settings import settings
from app.database.crud.reading.async_crud import Reading_crud
from app.database.crud.station.async_crud import Station_crud

WINDOW_HOURS = 48

# (parameter, comparison, threshold, severity, message) — most severe rule of a parameter first
RULES = [
    ("do", "<", 2.0, "critical", "Dissolved oxygen critically low — possible sewage discharge"),
    ("do", "<", 4.0, "warning", "Dissolved oxygen below 4 mg/L"),
    ("ammonium", ">", 4.0, "critical", "High ammonium — untreated sewage signature"),
    ("ammonium", ">", 2.0, "warning", "Ammonium above 2 mg/L"),
    ("turbidity", ">", 60, "warning", "Turbidity spike"),
    ("ec", ">", 1600, "warning", "Conductivity spike — possible industrial effluent"),
    ("ph", "<", 6.5, "warning", "pH below permissible range"),
    ("ph", ">", 8.5, "warning", "pH above permissible range"),
]


def _fails(value, op: str, thr: float) -> bool:
    if value is None:
        return False
    return value < thr if op == "<" else value > thr


def _make(st: dict, rule: tuple, ts: datetime, value: float, status: str, units: dict) -> dict:
    param, _, thr, sev, msg = rule
    aid = f"AL-{st['station_code']}-{param}-{ts.strftime('%m%d%H')}"
    # Acknowledgement is not stored yet; a stable share of active alerts is shown as acknowledged.
    if status == "active" and rng("ack", aid).random() < 0.3:
        status = "acknowledged"
    return {
        "id": aid, "station_id": st["station_code"], "station_name": st["name"], "parameter": param,
        "value": value, "threshold": thr, "unit": units.get(param, ""), "severity": sev, "message": msg,
        "raised_at": ts.isoformat(), "status": status, "sampling_triggered": sev == "critical",
    }


class alert_svc:

    async def list_alerts(db: AsyncSession, status: str | None, severity: str | None, station_id: str | None) -> list[dict]:
        crud = Station_crud(db)
        stations = await crud.get_stations()
        units = {p["key"]: p["unit"] for p in await crud.get_parameters()}
        readings = Reading_crud(db)
        last_ts = await readings.last_ts_per_station()
        now = datetime.now(timezone.utc)
        items: list[dict] = []

        by_param: dict[str, list] = {}
        for rule in RULES:
            by_param.setdefault(rule[0], []).append(rule)

        for st in stations:
            end = last_ts.get(st["station_code"])
            if end is None:
                continue
            gap = now - end
            if gap > timedelta(minutes=settings.OFFLINE_AFTER_MINUTES):
                items.append({
                    "id": f"AL-{st['station_code']}-offline", "station_id": st["station_code"], "station_name": st["name"],
                    "parameter": "telemetry", "value": round(gap.total_seconds() / 3600, 2),
                    "threshold": settings.OFFLINE_AFTER_MINUTES / 60, "unit": "h", "severity": "info",
                    "message": "Station not reporting — check power / telemetry", "raised_at": end.isoformat(),
                    "status": "active", "sampling_triggered": False,
                })
            rows = await readings.hourly_window(st["station_code"], end - timedelta(hours=WINDOW_HOURS), end)
            for param, rules in by_param.items():
                open_alert = None
                for r in rows:
                    hit = next((rule for rule in rules if _fails(r[param], rule[1], rule[2])), None)
                    if hit and (open_alert is None or (hit[3] == "critical" and open_alert[0][3] != "critical")):
                        open_alert = (hit, r["ts"], r[param])          # open, or escalate to critical
                    elif not hit and open_alert:
                        items.append(_make(st, open_alert[0], open_alert[1], open_alert[2], "resolved", units))
                        open_alert = None
                if open_alert:
                    items.append(_make(st, open_alert[0], open_alert[1], open_alert[2], "active", units))

        if status:
            items = [a for a in items if a["status"] == status]
        if severity:
            items = [a for a in items if a["severity"] == severity]
        if station_id:
            items = [a for a in items if a["station_id"] == station_id]
        return sorted(items, key=lambda a: a["raised_at"], reverse=True)
