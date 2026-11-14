"""Candidate landing sites and their long-term visibility figures.

AI-assisted: written by Claude (Anthropic), 2026-11-14.

Data comes from data/a3_region_visibility_stats.json, which was computed from
NASA LOLA average-visibility maps (see that file for sources and method).
Each Artemis III region is represented by one point: the pixel inside the
region with the best combined Sun and Earth visibility.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

MOON_RADIUS_M = 1_737_400.0
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "a3_region_visibility_stats.json"


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
    """One row per candidate site, with long-term Sun and Earth visibility (0-1)."""
    raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    rows = []
    for region in raw["artemis3_regions"]:
        spot = region["best_both"]
        x_km, y_km = latlon_to_polar_xy_km(spot["lat"], spot["lon"])
        rows.append(
            {
                "site": region["region"],
                "lat": spot["lat"],
                "lon": spot["lon"],
                "x_km": x_km,
                "y_km": y_km,
                "sun_long_term": spot["sun"],
                "earth_long_term": spot["earth"],
                "region_best_sun": region["best_sun"]["sun"],
                "region_best_earth": region["best_earth"],
            }
        )
    return pd.DataFrame(rows)


def rank_sites(sites: pd.DataFrame, min_sun: float, min_earth: float) -> pd.DataFrame:
    """Apply the long-term limits and rank the sites.

    Provisional score: the plain average of long-term Sun and Earth visibility.
    This is a placeholder until the date-specific scoring in
    docs/design-principles.md section 5 exists.
    """
    out = sites.copy()
    out["passes"] = (out["sun_long_term"] >= min_sun) & (out["earth_long_term"] >= min_earth)
    out["score"] = (out["sun_long_term"] + out["earth_long_term"]) / 2.0
    out = out.sort_values(["passes", "score"], ascending=[False, False]).reset_index(drop=True)
    out["rank"] = out.index + 1
    return out


def sites_as_records(min_sun: float = 0.5, min_earth: float = 0.5) -> list[dict]:
    """Ranked sites as plain dictionaries, for interfaces not written in Python."""
    ranked = rank_sites(load_sites(), min_sun, min_earth)
    return json.loads(ranked.to_json(orient="records"))


if __name__ == "__main__":
    # python src/sites.py > sites.json   (optional: min_sun min_earth, e.g. 0.6 0.5)
    import sys

    limits = [float(a) for a in sys.argv[1:3]]
    print(json.dumps(sites_as_records(*limits), indent=2))
