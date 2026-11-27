from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud.lab.async_crud import Lab_crud


class lab_svc:

    async def get_campaigns(db: AsyncSession) -> list[dict]:
        return [{"id": c["campaign_code"], "name": c["name"], "season": c["season"], "start": c["start_date"].isoformat(),
                 "end": c["end_date"].isoformat(), "type": c["campaign_type"], "trigger": c["trigger"],
                 "samples": c["samples"]} for c in await Lab_crud(db).get_campaigns()]

    async def get_compounds(db: AsyncSession) -> list[dict]:
        return [{"name": c["name"], "class": c["compound_class"], "marker_for": c["marker_for"], "pnec_ng_l": c["pnec_ng_l"]}
                for c in await Lab_crud(db).get_compounds()]

    async def get_samples(db: AsyncSession, campaign_code: str | None, station_code: str | None) -> list[dict]:
        crud = Lab_crud(db)
        samples = await crud.get_samples(campaign_code, station_code)
        dets: dict[str, list] = {}
        for d in await crud.get_detections([s["sample_code"] for s in samples]):
            dets.setdefault(d["sample_code"], []).append({
                "compound": d["compound"], "compound_class": d["compound_class"], "marker_for": d["marker_for"],
                "concentration_ng_l": d["concentration_ng_l"], "pnec_ng_l": d["pnec_ng_l"],
                "risk_quotient": round(d["concentration_ng_l"] / d["pnec_ng_l"], 2), "screening": d["screening"],
            })
        return [{
            "id": s["sample_code"], "campaign_id": s["campaign_code"], "station_id": s["station_code"], "site": s["site"],
            "matrix": s["matrix"], "lat": s["lat"], "lon": s["lon"], "collected_at": s["collected_at"].isoformat(),
            "collector": s["collector"],
            "detections": sorted(dets.get(s["sample_code"], []), key=lambda d: d["risk_quotient"], reverse=True),
        } for s in samples]

    async def get_apportionment(db: AsyncSession, campaign_code: str) -> list[dict]:
        crud = Lab_crud(db)
        if not await crud.campaign_exists(campaign_code):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Campaign {campaign_code} not found")
        sites: dict[str, dict] = {}
        for r in await crud.get_apportionment(campaign_code):
            site = sites.setdefault(r["station_code"], {"station_id": r["station_code"], "site": r["site"],
                                                         "campaign_id": campaign_code, "sources": []})
            site["sources"].append({"source": r["source"], "share_pct": r["share_pct"]})
        return list(sites.values())
