"""
Dummy-data model: deterministic river and groundwater readings.

Values are a function of (series key, timestamp) only. script/database/readings/* uses it to seed a year of
history; simulator_svc/live.py uses it to keep appending readings so the dashboard stays live. Remove both once
real devices push data through POST /api/ingest/readings.
"""
import hashlib
import math
import random
from datetime import datetime, timedelta, timezone


INTERVAL_MIN = 15  # IoT recording interval (Technical Doc 2.2)

# Baseline (mean) value per profile; generator adds diurnal cycle + noise.
PROFILE_BASE: dict[str, dict[str, float]] = {
    "clean":    {"ph": 7.6, "do": 7.4, "ec": 420, "turbidity": 8, "orp": 260, "nitrate": 1.8, "ammonium": 0.15,
                 "phosphate": 0.08, "chlorophyll": 6, "bod": 1.8, "cod": 12, "water_level": 1.4, "flow": 6.5},
    "moderate": {"ph": 7.5, "do": 5.0, "ec": 680, "turbidity": 18, "orp": 180, "nitrate": 4.5, "ammonium": 1.0,
                 "phosphate": 0.25, "chlorophyll": 14, "bod": 4.2, "cod": 24, "water_level": 1.9, "flow": 11},
    "poor":     {"ph": 7.3, "do": 3.6, "ec": 1050, "turbidity": 34, "orp": 90, "nitrate": 8.2, "ammonium": 2.1,
                 "phosphate": 0.6, "chlorophyll": 26, "bod": 8.5, "cod": 48, "water_level": 2.3, "flow": 15},
    "severe":   {"ph": 7.1, "do": 1.4, "ec": 1480, "turbidity": 55, "orp": -40, "nitrate": 11.5, "ammonium": 5.8,
                 "phosphate": 1.3, "chlorophyll": 38, "bod": 22, "cod": 96, "water_level": 2.1, "flow": 14},
}


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def floor_to_interval(ts: datetime, minutes: int = INTERVAL_MIN) -> datetime:
    return ts.replace(minute=(ts.minute // minutes) * minutes, second=0, microsecond=0)


def rng(*key) -> random.Random:
    """Seeded RNG from any hashable key parts."""
    seed = int(hashlib.md5("|".join(map(str, key)).encode()).hexdigest()[:12], 16)
    return random.Random(seed)


def _diurnal(ts: datetime, peak_hour: float = 15.0) -> float:
    """-1..1 daily cycle, peak at `peak_hour` local (IST)."""
    hour_ist = (ts.hour + ts.minute / 60 + 5.5) % 24
    return math.cos((hour_ist - peak_hour) / 24 * 2 * math.pi)


def _season(ts: datetime) -> float:
    """0..1 monsoon intensity (peaks mid-August)."""
    doy = ts.timetuple().tm_yday
    return max(0.0, math.cos((doy - 225) / 365 * 2 * math.pi)) ** 3


def _event(station_id: str, ts: datetime) -> float:
    """Occasional sewage-discharge pulse (0..1). About one 3-hour pulse every few days."""
    block = int(ts.timestamp() // (3 * 3600))
    r = rng("event", station_id, block)
    if r.random() < 0.06:
        return 0.6 + 0.4 * r.random()
    return 0.0


def river_reading(station_id: str, profile: str, ts: datetime) -> dict[str, float]:
    base = PROFILE_BASE[profile]
    r = rng("rv", station_id, int(ts.timestamp()))
    d = _diurnal(ts)
    s = _season(ts)
    e = _event(station_id, ts)
    n = lambda scale: r.gauss(0, scale)  # noqa: E731

    rain = 0.0
    if r.random() < 0.02 + 0.25 * s:
        rain = round(abs(r.gauss(0, 1.5 + 6 * s)), 1)

    temp = 22 + 6 * math.cos((ts.timetuple().tm_yday - 160) / 365 * 2 * math.pi) + 1.5 * d + n(0.2)
    do = base["do"] * (1 + 0.18 * d) * (1 - 0.7 * e) + n(0.15)
    return {
        "ph": round(base["ph"] + 0.15 * d - 0.3 * e + n(0.05), 2),
        "do": round(max(0.0, do), 2),
        "ec": round(base["ec"] * (1 + 0.35 * e - 0.3 * s) + n(15), 0),
        "turbidity": round(max(0.5, base["turbidity"] * (1 + 1.5 * s + 0.8 * e) + n(1.5)), 1),
        "temperature": round(temp, 1),
        "orp": round(base["orp"] + 30 * d - 120 * e + n(8), 0),
        "nitrate": round(max(0.0, base["nitrate"] * (1 + 0.4 * s + 0.3 * e) + n(0.2)), 2),
        "ammonium": round(max(0.0, base["ammonium"] * (1 + 1.6 * e) + n(0.05)), 2),
        "phosphate": round(max(0.0, base["phosphate"] * (1 + 0.8 * e) + n(0.02)), 3),
        "chlorophyll": round(max(0.0, base["chlorophyll"] * (1 + 0.25 * d) + n(0.8)), 1),
        "bod": round(max(0.2, base["bod"] * (1 + 1.2 * e) + n(0.3)), 1),
        "cod": round(max(2, base["cod"] * (1 + 1.1 * e) + n(1.5)), 0),
        "water_level": round(base["water_level"] * (1 + 1.8 * s) + 0.03 * d + n(0.01), 2),
        "flow": round(max(0.3, base["flow"] * (1 + 6 * s) + n(0.3)), 1),
        "rainfall": rain,
        "air_temp": round(temp + 4 + 4 * d + n(0.4), 1),
        "humidity": round(min(100, max(20, 62 + 25 * s - 15 * d + n(2))), 0),
        # device health
        "battery_v": round(12.2 + 0.6 * d + n(0.05), 2),
        "signal_dbm": round(-78 + n(6), 0),
    }


def well_reading(well_id: str, ts: datetime) -> dict[str, float]:
    r = rng("gw", well_id, int(ts.timestamp()))
    s = _season(ts)
    base_depth = {"GW-01": 8.5, "GW-02": 14.2, "GW-03": 9.8, "GW-04": 7.1}[well_id]
    base_ec = {"GW-01": 620, "GW-02": 780, "GW-03": 1650, "GW-04": 840}[well_id]
    return {
        "depth_to_water_m": round(base_depth - 3.2 * s + r.gauss(0, 0.02), 2),
        "ec": round(base_ec * (1 - 0.1 * s) + r.gauss(0, 8), 0),
        "temperature": round(24.5 + 0.8 * math.sin(ts.timetuple().tm_yday / 365 * 2 * math.pi) + r.gauss(0, 0.05), 2),
    }


def timestamps(hours: int, step_min: int = INTERVAL_MIN, end: datetime | None = None) -> list[datetime]:
    end = floor_to_interval(end or now_utc(), step_min)
    count = max(1, int(hours * 60 / step_min))
    return [end - timedelta(minutes=step_min * i) for i in range(count - 1, -1, -1)]
