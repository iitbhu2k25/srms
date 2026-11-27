"""Geodesy helpers and the dummy mission simulation for the SMART-STREAM boat."""
import math
from datetime import datetime, timedelta


def haversine(a, b) -> float:
    r = 6371000
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def bearing(a, b) -> float:
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dl = math.radians(b[1] - a[1])
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def simulate(waypoints: list[dict], loop_minutes: int, now: datetime) -> dict:
    """Position of a boat that runs the mission once every `loop_minutes`, starting on the hour."""
    pts = [(w["lat"], w["lon"]) for w in waypoints]
    legs = [haversine(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(legs)
    elapsed_min = (now.minute + now.second / 60) % loop_minutes
    progress = elapsed_min / loop_minutes
    travelled = progress * total

    acc, leg = 0.0, 0
    while leg < len(legs) - 1 and acc + legs[leg] < travelled:
        acc += legs[leg]
        leg += 1
    frac = min(1.0, (travelled - acc) / legs[leg]) if legs[leg] else 1.0
    a, b = pts[leg], pts[leg + 1]
    pos = (a[0] + (b[0] - a[0]) * frac, a[1] + (b[1] - a[1]) * frac)
    near_wp = frac < 0.04 and waypoints[leg]["action"] == "sample"
    reached = leg + (1 if frac >= 0.999 else 0)

    wps = []
    for i, w in enumerate(waypoints):
        if i == leg and near_wp:
            st = "active"
        elif i <= reached:
            st = "done"
        elif i == leg + 1:
            st = "active"
        else:
            st = "pending"
        wps.append({**w, "status": st})

    loop_start = now.replace(second=0, microsecond=0) - timedelta(minutes=int(elapsed_min))
    bottles = []
    for w_idx, w in enumerate(waypoints):
        if not w["bottle"]:
            continue
        filled = w_idx < leg or (w_idx == leg and not near_wp)
        at = loop_start + timedelta(minutes=(sum(legs[:w_idx]) / total) * loop_minutes) if total else loop_start
        bottles.append({"id": w["bottle"], "volume_ml": 500, "filled": filled, "waypoint": w["seq"],
                        "filled_at": at.isoformat() if filled else None})

    return {
        "lat": pos[0], "lon": pos[1], "heading_deg": round(bearing(a, b), 1), "progress": progress,
        "state": "sampling" if near_wp else ("returning" if progress > 0.97 else "navigating"),
        "waypoints": wps, "bottles": sorted(bottles, key=lambda x: x["id"]),
        "track": [list(p) for p in pts[: leg + 1]] + [list(pos)],
    }
