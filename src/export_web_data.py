"""Export planner results for the static web front end (docs/index.html).

AI-assisted: written by Claude (Anthropic), 2026-11-15.

For every landing date 2027-2030 at 00:00 UTC and mission lengths of 7, 14
and 28 days, store per site: Sun and Earth mission-window ratios, and their
worst case if the landing slips by up to 14 days. The same cumulative sums as
planner.conditions are used, so values equal planner.rank_for_date at 00:00 UTC.

Values are stored as whole hours (Sun or Earth visible) per mission window,
little-endian uint16, base64; ratio = hours / hours_per_window. Integer counts
and the unrounded slope let the page rank exactly as the planner does.

Run:  python src/export_web_data.py   ->  docs/data/sites.json
"""
from __future__ import annotations

import base64
import datetime as dt
import json
from pathlib import Path

import numpy as np

import planner

WINDOWS = (7, 14, 28)
SLIP_DAYS = 14
OUT = Path(__file__).resolve().parents[1] / "docs/data/sites.json"


def pack(a: np.ndarray, hours: int) -> str:
    v = np.rint(np.asarray(a, dtype=float) * hours).astype("<u2")
    return base64.b64encode(v.tobytes()).decode("ascii")


def main() -> None:
    first, last = dt.date(2027, 1, 1), dt.date(2030, 12, 31)
    lk = planner.build_lookup(first, last)
    per_day = int(24 / planner.STEP_HOURS)
    n_days = (last - first).days + 1
    starts = np.arange(n_days) * per_day
    max_start = lk.cum_sun.shape[1] - 1
    sites = lk.sites
    out = {
        "note": "AI-generated data export (Claude, Anthropic) from src/planner.py; NASA LOLA-based. "
                "Values: visible hours per mission window, uint16 little-endian, base64; one value per landing date from first_date.",
        "first_date": first.isoformat(), "n_days": n_days, "landing_hour_utc": 0,
        "slip_days": SLIP_DAYS, "windows": list(WINDOWS),
        "hours_per_window": {str(w): int(w * 24 / planner.STEP_HOURS) for w in WINDOWS},
        "limits_default": {"min_sun_long_term": 0.5, "min_earth_long_term": 0.5,
                           "min_sun_window": 0.95, "min_earth_window": 0.95},
        "map_extent_km": 210,
        "sites": [],
    }
    series = {}
    for w_days in WINDOWS:
        w = int(w_days * 24 / planner.STEP_HOURS)
        sun = (lk.cum_sun[:, starts + w] - lk.cum_sun[:, starts]) / w
        earth = (lk.cum_earth[:, starts + w] - lk.cum_earth[:, starts]) / w
        # worst case over landing shifted -slip..+slip days, same rule as planner.conditions
        sw, ew = np.full_like(sun, np.inf), np.full_like(earth, np.inf)
        for d in range(-SLIP_DAYS, SLIP_DAYS + 1):
            s2 = starts + d * per_day
            ok = (s2 >= 0) & (s2 + w <= max_start)
            s2c = np.clip(s2, 0, max_start - w)
            ss = (lk.cum_sun[:, s2c + w] - lk.cum_sun[:, s2c]) / w
            ee = (lk.cum_earth[:, s2c + w] - lk.cum_earth[:, s2c]) / w
            sw = np.where(ok, np.minimum(sw, ss), sw)
            ew = np.where(ok, np.minimum(ew, ee), ew)
        series[w_days] = (sun, earth, sw, ew)
    for k, r in enumerate(sites.itertuples()):
        out["sites"].append({
            "name": r.site, "lat": round(r.lat, 4), "lon": round(r.lon, 4),
            "x_km": round(r.x_km, 3), "y_km": round(r.y_km, 3), "height_m": round(r.height_m),
            "sun_long_term": round(r.sun_long_term, 4), "earth_long_term": round(r.earth_long_term, 4),
            "slope_mean_deg": float(r.slope_mean_deg), "slope_max_deg": float(r.slope_max_deg),
            "series": {str(w): {n: pack(a[k], int(w * 24 / planner.STEP_HOURS)) for n, a in zip(("sun", "earth", "sun_worst", "earth_worst"), series[w])}
                       for w in WINDOWS},
        })
    OUT.write_text(json.dumps(out, separators=(",", ":")))
    print(OUT, OUT.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
