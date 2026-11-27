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


def simulate(waypoints: list[dict], loop_minutes: int, now: datetime, path: list[list[float]] | None = None) -> dict:
    """
    Position of a boat that runs the mission once every `loop_minutes`, starting on the hour. It travels along
    `path` ([[lat, lon], ...], e.g. the river channel); without a path it goes straight between waypoints.
    """
    pts = [tuple(p) for p in path] if path and len(path) > 1 else [(w["lat"], w["lon"]) for w in waypoints]
    cum = [0.0]
    for i in range(1, len(pts)):
        cum.append(cum[-1] + haversine(pts[i - 1], pts[i]))

    def along(lat, lon):          # distance along the path of the vertex nearest to a point
        i = min(range(len(pts)), key=lambda k: (pts[k][0] - lat) ** 2 + (pts[k][1] - lon) ** 2)
        return cum[i]

    wp_d = [along(w["lat"], w["lon"]) for w in waypoints]
    start_d, end_d = wp_d[0], wp_d[-1]
    elapsed_min = (now.minute + now.second / 60) % loop_minutes
    progress = elapsed_min / loop_minutes
    d = start_d + progress * (end_d - start_d)

    # interpolate the position on the path
    seg = next((i for i in range(1, len(cum)) if cum[i] >= d), len(cum) - 1)
    a, b = pts[seg - 1], pts[seg]
    span = cum[seg] - cum[seg - 1]
    f = (d - cum[seg - 1]) / span if span else 0.0
    pos = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)

    leg = max(i for i in range(len(wp_d)) if wp_d[i] <= d + 1e-6)          # last waypoint passed
    leg = min(leg, len(waypoints) - 2)
    near_wp = waypoints[leg]["action"] == "sample" and 0 <= d - wp_d[leg] < 0.04 * (end_d - start_d)

    wps = []
    for i, w in enumerate(waypoints):
        if i < leg or (i == leg and not near_wp):
            st = "done"
        elif i == leg or (i == leg + 1 and not near_wp):
            st = "active"                     # sampling here, or heading here next
        else:
            st = "pending"
        wps.append({**w, "status": st})

    loop_start = now.replace(second=0, microsecond=0) - timedelta(minutes=int(elapsed_min))
    total = (end_d - start_d) or 1.0
    bottles = []
    for i, w in enumerate(waypoints):
        if not w["bottle"]:
            continue
        filled = wp_d[i] < d and not (i == leg and near_wp)
        at = loop_start + timedelta(minutes=(wp_d[i] - start_d) / total * loop_minutes)
        bottles.append({"id": w["bottle"], "volume_ml": 500, "filled": filled, "waypoint": w["seq"],
                        "filled_at": at.isoformat() if filled else None})

    first = next(i for i in range(len(cum)) if cum[i] >= start_d)
    track = [list(p) for p in pts[first:seg]] + [list(pos)]
    return {
        "lat": pos[0], "lon": pos[1], "heading_deg": round(bearing(a, b), 1), "progress": progress,
        "state": "sampling" if near_wp else ("returning" if progress > 0.97 else "navigating"),
        "waypoints": wps, "bottles": sorted(bottles, key=lambda x: x["id"]), "track": track,
        "route": [list(p) for p in pts[first:next(i for i in range(len(cum)) if cum[i] >= end_d) + 1]],
    }
