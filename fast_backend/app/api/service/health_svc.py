"""River Health Index (0-100) and limit checks. Weights/thresholds are placeholders to be agreed with the team."""


# (parameter, weight, value scoring 100, value scoring 0); pH (weight 0.10) is scored separately.
WEIGHTS = [
    ("do", 0.35, 8.0, 2.0),
    ("bod", 0.20, 2.0, 15.0),
    ("ammonium", 0.20, 0.5, 5.0),
    ("turbidity", 0.10, 10.0, 80.0),
    ("ec", 0.05, 750.0, 2500.0),
]


def _lin(value: float, good: float, bad: float) -> float:
    """100 at `good`, 0 at `bad`, linear in between (works in either direction)."""
    score = (value - bad) / (good - bad) * 100
    return max(0.0, min(100.0, score))


class health_svc:

    def health_index(r: dict) -> float:
        """Weighted mean of the sub-scores that are present (a partial reading is not penalised for gaps)."""
        parts = []
        ph = r.get("ph")
        if ph is not None:
            parts.append((0.10, 100.0 if 6.5 <= ph <= 8.5 else max(0.0, 100 - 40 * min(abs(ph - 6.5), abs(ph - 8.5)))))
        for key, weight, good, bad in WEIGHTS:
            if r.get(key) is not None:
                parts.append((weight, _lin(r[key], good, bad)))
        if not parts:
            return 0.0
        return round(sum(w * v for w, v in parts) / sum(w for w, _ in parts), 1)

    def category(rhi: float) -> str:
        if rhi >= 80:
            return "good"
        if rhi >= 60:
            return "moderate"
        if rhi >= 40:
            return "poor"
        return "critical"

    def exceedances(r: dict, parameters: list[dict]) -> list[str]:
        out = []
        for p in parameters:
            v = r.get(p["key"])
            if v is None:
                continue
            if (p["min_limit"] is not None and v < p["min_limit"]) or (p["max_limit"] is not None and v > p["max_limit"]):
                out.append(p["key"])
        return out
