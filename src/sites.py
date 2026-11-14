"""Candidate landing sites: position, long-term visibility and terrain skyline.

AI-assisted: written by Claude (Anthropic), 2026-11-14.

Source file: data/terrain_horizons.txt (see its header for the NASA products
used). Each Artemis III region is represented by one point: the 60 m pixel in
the region with the best combined long-term Sun and Earth visibility.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

MOON_RADIUS_M = 1_737_400.0
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAST_HEIGHT_M = 2.0  # the skylines were computed from 2 m above the surface


def latlon_to_polar_xy_km(lat_deg: float, lon_deg: float) -> tuple[float, float]:
    """South polar stereographic projection, true at the pole.

    Longitude 0 points to +y (towards Earth), east longitude is positive,
    matching the NASA LOLA polar products. Returns kilometres.
    """
    colat = math.radians(90.0 + lat_deg)  # angle from the south pole
    r = 2.0 * MOON_RADIUS_M * math.tan(colat / 2.0)
    lon = math.radians(lon_deg)
    return r * math.sin(lon) / 1000.0, r * math.cos(lon) / 1000.0


def load_sites() -> pd.DataFrame:
    """One row per candidate site.

    Columns: site, lat, lon (degrees, east positive), x_km, y_km (polar map),
    sun_long_term, earth_long_term (0-1, NASA LOLA, 18.6-year average),
    height_m (surface height above the 1737.4 km sphere),
    skyline (numpy array of 360 terrain elevation angles in degrees, index =
    azimuth clockwise from lunar north),
    sun_offset_deg, earth_offset_deg (calibration, see planner.py).
    """
    calib = json.loads((DATA_DIR / "horizon_calibration.json").read_text(encoding="utf-8"))["sites"]
    rows = []
    for line in (DATA_DIR / "terrain_horizons.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        name, lat, lon, sun, earth, height, profile = line.split("|")
        lat, lon = float(lat), float(lon)
        x_km, y_km = latlon_to_polar_xy_km(lat, lon)
        skyline = np.array(profile.split(), dtype=float) / 100.0
        if skyline.size != 360:
            raise ValueError(f"{name}: expected 360 skyline values, got {skyline.size}")
        rows.append(
            {
                "site": name, "lat": lat, "lon": lon, "x_km": x_km, "y_km": y_km,
                "sun_long_term": float(sun), "earth_long_term": float(earth),
                "height_m": float(height), "skyline": skyline,
                "sun_offset_deg": calib[name]["sun_offset_deg"],
                "earth_offset_deg": calib[name]["earth_offset_deg"],
            }
        )
    return pd.DataFrame(rows)


def rank_sites(sites: pd.DataFrame, min_sun: float, min_earth: float) -> pd.DataFrame:
    """Rank on long-term values only (no date). Prefer planner.rank_for_date."""
    out = sites.copy()
    out["passes"] = (out["sun_long_term"] >= min_sun) & (out["earth_long_term"] >= min_earth)
    out["score"] = (out["sun_long_term"] + out["earth_long_term"]) / 2.0
    out = out.sort_values(["passes", "score"], ascending=[False, False]).reset_index(drop=True)
    out["rank"] = out.index + 1
    return out


def sites_as_records(min_sun: float = 0.5, min_earth: float = 0.5) -> list[dict]:
    """Ranked sites as plain dictionaries, for interfaces not written in Python."""
    ranked = rank_sites(load_sites(), min_sun, min_earth)
    ranked["skyline"] = ranked["skyline"].apply(lambda a: [round(float(v), 2) for v in a])
    return json.loads(ranked.to_json(orient="records"))


if __name__ == "__main__":
    # python src/sites.py > sites.json   (optional: min_sun min_earth, e.g. 0.6 0.5)
    import sys

    limits = [float(a) for a in sys.argv[1:3]]
    print(json.dumps(sites_as_records(*limits), indent=2))
