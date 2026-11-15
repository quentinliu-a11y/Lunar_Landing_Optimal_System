"""Export planner results for the static web front end (docs/index.html).

AI-assisted: written by Claude (Anthropic), 2026-11-15.

For every site, the number of hours in each UTC day (2027-01-01 onward) with
the Sun visible and with Earth visible, taken from the same hourly lookup and
cumulative sums as src/planner.py. The page adds whole days to get any mission
length from 1 to 60 days starting at 00:00 UTC, and the slip worst case, so
its results equal planner.rank_for_date at 00:00 UTC.

Run:  python src/export_web_data.py   ->  docs/data/sites.json
"""
from __future__ import annotations

import base64
import datetime as dt
import json
from pathlib import Path

import numpy as np

import planner

SLIP_DAYS = 14
OUT = Path(__file__).resolve().parents[1] / "docs/data/sites.json"


def main() -> None:
    first, last = dt.date(2027, 1, 1), dt.date(2030, 12, 31)
    lk = planner.build_lookup(first, last)
    per_day = int(24 / planner.STEP_HOURS)
    days_avail = (lk.cum_sun.shape[1] - 1) // per_day      # whole days a window may cover
    edges = np.arange(days_avail + 1) * per_day
    sun_day = np.rint(np.diff(lk.cum_sun[:, edges], axis=1)).astype(np.uint8)
    earth_day = np.rint(np.diff(lk.cum_earth[:, edges], axis=1)).astype(np.uint8)
    out = {
        "note": "AI-generated data export (Claude, Anthropic) from src/planner.py, NASA LOLA-based. "
                "sun_day / earth_day: hours (0-24) with the Sun / Earth visible in each UTC day from first_date, uint8, base64.",
        "first_date": first.isoformat(), "n_days": (last - first).days + 1, "days_available": int(days_avail),
        "hours_per_day": per_day, "max_window_days": lk.max_window_days, "slip_days": SLIP_DAYS,
        "limits_default": {"min_sun_long_term": 0.5, "min_earth_long_term": 0.5,
                           "min_sun_window": 0.95, "min_earth_window": 0.95},
        "map_extent_km": 210,
        "sites": [],
    }
    for k, r in enumerate(lk.sites.itertuples()):
        out["sites"].append({
            "name": r.site, "lat": round(r.lat, 4), "lon": round(r.lon, 4),
            "x_km": round(r.x_km, 3), "y_km": round(r.y_km, 3), "height_m": round(r.height_m),
            "sun_long_term": float(r.sun_long_term), "earth_long_term": float(r.earth_long_term),
            "slope_mean_deg": float(r.slope_mean_deg), "slope_max_deg": float(r.slope_max_deg),
            "sun_day": base64.b64encode(sun_day[k].tobytes()).decode("ascii"),
            "earth_day": base64.b64encode(earth_day[k].tobytes()).decode("ascii"),
        })
    OUT.write_text(json.dumps(out, separators=(",", ":")))
    print(OUT, OUT.stat().st_size, "bytes; days available", days_avail)


if __name__ == "__main__":
    main()
