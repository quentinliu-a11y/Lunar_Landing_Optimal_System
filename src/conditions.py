"""Conditions at a landing site for a chosen landing date.

AI-assisted: written by Claude (Anthropic), 2026-11-14.

Input : a site (latitude, longitude, optional terrain horizon), a landing
        date/time in UTC and a mission length in days.
Output: a timeline of Sun and Earth positions over the mission, and summary
        figures: sunlight ratio, Earth-contact ratio, longest darkness,
        longest loss of contact, time until sunset and Earthset.

"Visible" means any part of the disc is above the horizon, the same
definition the NASA LOLA visibility maps use.

The horizon is either
- a terrain horizon: elevation angle of the skyline for each azimuth
  (data/site_horizons.json), or
- a smooth-sphere horizon at 0 degrees when no terrain horizon is given.
  That case ignores all terrain and must be labelled as an approximation.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import numpy as np

from ephemeris import hourly_times, sky_positions

HORIZON_FILE = Path(__file__).resolve().parent.parent / "data" / "site_horizons.json"
SEARCH_DAYS = 60  # how far ahead to look for the next sunset / Earthset


def load_horizons() -> dict:
    """Terrain horizons per site name, or an empty dict if the file is absent."""
    if not HORIZON_FILE.exists():
        return {}
    raw = json.loads(HORIZON_FILE.read_text(encoding="utf-8"))
    return raw["sites"]


def horizon_at(azimuth_deg: np.ndarray, horizon: dict | None) -> np.ndarray:
    """Skyline elevation (degrees) in each given direction."""
    if not horizon:
        return np.zeros_like(azimuth_deg)
    step = horizon["azimuth_step_deg"]
    profile = np.asarray(horizon["elevation_deg"], dtype=float)
    idx = np.floor((azimuth_deg % 360.0) / step).astype(int) % len(profile)
    return profile[idx]


def _longest_run_hours(flags: np.ndarray, step_hours: float) -> float:
    """Longest unbroken stretch where flags is True, in hours."""
    best = run = 0
    for f in flags:
        run = run + 1 if f else 0
        best = max(best, run)
    return best * step_hours


def _hours_until_false(flags: np.ndarray, step_hours: float) -> float | None:
    """Hours from the start until flags first becomes False.
    0 if already False at the start; None if it stays True throughout."""
    off = np.flatnonzero(~flags)
    return None if off.size == 0 else float(off[0] * step_hours)


def timeline(lat: float, lon: float, start_utc: dt.datetime, days: float,
             horizon: dict | None = None, step_hours: float = 1.0) -> dict:
    """Sun and Earth positions and visibility at each time step."""
    times = hourly_times(start_utc, days, step_hours)
    height_km = (horizon or {}).get("height_m", 0.0) / 1000.0
    sky = sky_positions(lat, lon, times, height_km=height_km)
    sun_horizon = horizon_at(sky["sun_az"], horizon)
    earth_horizon = horizon_at(sky["earth_az"], horizon)
    return {
        "time": times,
        "sun_az": sky["sun_az"],
        "sun_el": sky["sun_el"],
        "earth_az": sky["earth_az"],
        "earth_el": sky["earth_el"],
        "sun_horizon": sun_horizon,
        "earth_horizon": earth_horizon,
        "sun_visible": sky["sun_el"] + sky["sun_radius_deg"] > sun_horizon,
        "earth_visible": sky["earth_el"] + sky["earth_radius_deg"] > earth_horizon,
    }


def site_conditions(lat: float, lon: float, landing_utc: dt.datetime, window_days: float,
                    horizon: dict | None = None, step_hours: float = 1.0) -> dict:
    """Summary of a site for a landing date. All ratios are 0-1, durations in hours."""
    tl = timeline(lat, lon, landing_utc, window_days, horizon, step_hours)
    sun, earth = tl["sun_visible"], tl["earth_visible"]

    # Look further ahead for the next sunset / Earthset than the mission window.
    ahead = timeline(lat, lon, landing_utc, SEARCH_DAYS, horizon, step_hours)

    return {
        "terrain_horizon_used": bool(horizon),
        "sun_ratio": float(sun.mean()),
        "earth_ratio": float(earth.mean()),
        "both_ratio": float((sun & earth).mean()),
        "longest_dark_h": _longest_run_hours(~sun, step_hours),
        "longest_no_contact_h": _longest_run_hours(~earth, step_hours),
        "sun_visible_at_landing": bool(sun[0]),
        "earth_visible_at_landing": bool(earth[0]),
        "sun_el_at_landing": float(tl["sun_el"][0]),
        "sun_az_at_landing": float(tl["sun_az"][0]),
        "earth_el_at_landing": float(tl["earth_el"][0]),
        "earth_az_at_landing": float(tl["earth_az"][0]),
        "max_sun_el": float(tl["sun_el"].max()),
        "mean_sun_el_when_lit": float(tl["sun_el"][sun].mean()) if sun.any() else None,
        "hours_to_sunset": _hours_until_false(ahead["sun_visible"], step_hours),
        "hours_to_earthset": _hours_until_false(ahead["earth_visible"], step_hours),
        "search_days": SEARCH_DAYS,
    }
