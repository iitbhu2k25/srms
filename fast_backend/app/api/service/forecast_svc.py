"""
Bacterial (faecal coliform) forecast — PLACEHOLDER for the AI model in the proposal.

Uses the latest organic-load readings and rainfall as a crude proxy; replace with the trained model's
output (e.g. a forecasts table written by a daily job).
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.service.simulator_svc.generator import rng
from app.api.service.station_svc import station_svc
from app.database.crud.reading.async_crud import Reading_crud


class forecast_svc:

    async def get_forecast(db: AsyncSession, station_code: str) -> dict:
        await station_svc.get_station_or_404(db, station_code)
        last = await Reading_crud(db).latest(station_code) or {}
        bod, nh4, rain = last.get("bod") or 3, last.get("ammonium") or 0.5, last.get("rainfall") or 0
        base = 120 * (bod ** 1.6) * (1 + nh4) * (1 + rain / 5)
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        days = []
        for i in range(1, 4):
            d = today + timedelta(days=i)
            r = rng("fc", station_code, d.date())
            mpn = int(base * (0.7 + r.random() * 0.6))
            cat = "Safe" if mpn <= 500 else "Caution" if mpn <= 2500 else "Unsafe"
            days.append({"date": d.date().isoformat(), "fecal_coliform_mpn": mpn, "category": cat,
                         "confidence": round(0.88 - 0.07 * i + r.random() * 0.03, 2)})
        return {"station_id": station_code, "model": "Placeholder proxy (BOD, NH₄, rainfall) — AI model pending",
                "issued": today.isoformat(), "days": days}
