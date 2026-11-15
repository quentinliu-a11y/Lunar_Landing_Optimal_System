"""Export hourly Sun/Earth directions and visibility per site for the 3D scene.

AI-assisted: written by Claude (Anthropic), 2026-11-15.

Writes docs/data/sim_sites.json (site facts and terrain skylines) and
docs/data/sky/<n>.bin, one per site: for every hour from 2027-01-01 00:00 UTC,
little-endian int16 [sun_az, sun_el, earth_az, earth_el] in hundredths of a
degree (azimuths stored as az - 180), then one uint8 per hour with bit 0 =
Sun visible, bit 1 = Earth visible, bit 2 = lunar eclipse. Values come straight
from planner.build_lookup, so visibility equals the analysis app's.

Run:  python src/export_sim_data.py
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import numpy as np

import planner

OUT = Path(__file__).resolve().parents[1] / "docs/data"


def main() -> None:
    lk = planner.build_lookup(dt.date(2027, 1, 1), dt.date(2030, 12, 31))
    (OUT / "sky").mkdir(parents=True, exist_ok=True)
    n = lk.sun_el.shape[1]
    sites = []
    for k, r in enumerate(lk.sites.itertuples()):
        rec = np.empty((n, 4), "<i2")
        rec[:, 0] = np.rint(lk.sun_az[k] * 100 - 18000)
        rec[:, 1] = np.rint(lk.sun_el[k] * 100)
        rec[:, 2] = np.rint(lk.earth_az[k] * 100 - 18000)
        rec[:, 3] = np.rint(lk.earth_el[k] * 100)
        flags = (lk.sun_up[k].astype(np.uint8) | (lk.earth_up[k].astype(np.uint8) << 1)
                 | ((lk.eclipse[k] > 0).astype(np.uint8) << 2))
        (OUT / "sky" / f"{k}.bin").write_bytes(rec.tobytes() + flags.astype(np.uint8).tobytes())
        sites.append({
            "id": k, "name": r.site, "lat": round(r.lat, 4), "lon": round(r.lon, 4),
            "skyline_cdeg": [int(round(v * 100)) for v in r.skyline],
            "sun_offset_deg": round(float(r.sun_offset_deg), 3), "earth_offset_deg": round(float(r.earth_offset_deg), 3),
            "slope_mean_deg": round(float(r.slope_mean_deg), 2), "slope_max_deg": round(float(r.slope_max_deg), 2),
            "sun_long_term": round(float(r.sun_long_term), 4), "earth_long_term": round(float(r.earth_long_term), 4),
            "height_m": int(round(r.height_m)),
        })
    meta = {"note": "AI-generated export (Claude, Anthropic) from src/planner.py for the 3D scene. NASA LOLA terrain; "
                    "Sun/Earth from ERFA, checked against JPL Horizons.",
            "start_utc": "2027-01-01T00:00:00Z", "hours": int(n), "mast_height_m": 2, "sites": sites}
    (OUT / "sim_sites.json").write_text(json.dumps(meta, separators=(",", ":")))
    print("hours", n, "per-site bytes", (OUT / "sky" / "0.bin").stat().st_size)


if __name__ == "__main__":
    main()
