"""Date-specific conditions and ranking for the candidate landing sites.

AI-assisted: written by Claude (Anthropic), 2026-11-14.

Design for speed (so date sliders and animations stay smooth):
- build_lookup() does the heavy work ONCE: an hourly Sun/Earth timeline for
  every site over the whole date range, then per-day mission-window results.
- After that, conditions for any landing date are a table lookup, and the
  hourly curve for a chart is a slice of an array. Nothing is recomputed
  when the user moves the date.

IMPORTANT LIMITATION: visibility here uses a FLAT horizon (a smooth sphere).
Real terrain hides the Sun and Earth more often, so the mission-window
ratios are upper bounds. The long-term LOLA figures in sites.py do include
terrain. Interfaces must label these values "flat-horizon estimate".

Definitions:
- Sun visible   : any part of the Sun's disc above the flat horizon
                  (same definition as the NASA LOLA illumination maps).
- Earth visible : Earth's centre above the flat horizon.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import numpy as np
import pandas as pd

from ephemeris import SUN_RADIUS_KM, _az_el, _to_jd_tt, sun_earth_from_moon_centre
from sites import load_sites

STEP_HOURS = 1.0


@dataclass
class Lookup:
    sites: pd.DataFrame          # one row per site (from sites.load_sites)
    times: np.ndarray            # hourly UTC times, datetime64[ms], length T
    sun_el: np.ndarray           # (n_sites, T) degrees, Sun centre
    earth_el: np.ndarray         # (n_sites, T) degrees, Earth centre
    sun_az: np.ndarray           # (n_sites, T) degrees
    earth_az: np.ndarray         # (n_sites, T) degrees
    sun_up: np.ndarray           # (n_sites, T) bool
    earth_up: np.ndarray         # (n_sites, T) bool
    hours_to_sunset: np.ndarray  # (n_sites, T) hours until the Sun next sets (0 if down, nan if beyond range)
    hours_to_earthset: np.ndarray
    start: dt.date
    end: dt.date                 # last allowed landing date
    max_window_days: int


def _hours_until_false(up: np.ndarray) -> np.ndarray:
    """For each hour, how many hours until `up` next becomes False."""
    out = np.full(up.shape, np.nan)
    idx = np.arange(up.shape[1])
    for s in range(up.shape[0]):
        false_at = np.flatnonzero(~up[s])
        if false_at.size == 0:
            continue
        pos = np.searchsorted(false_at, idx)          # first False at or after each hour
        ok = pos < false_at.size
        out[s, ok] = (false_at[pos[ok]] - idx[ok]) * STEP_HOURS
    return out


def build_lookup(start: dt.date, end: dt.date, max_window_days: int = 60) -> Lookup:
    """Precompute everything for landing dates from `start` to `end` inclusive."""
    sites = load_sites()
    n_hours = int(((end - start).days + 1 + max_window_days) * 24 / STEP_HOURS) + 1
    t0 = np.datetime64(dt.datetime.combine(start, dt.time(0)), "ms")
    times = t0 + (np.arange(n_hours) * STEP_HOURS * 3_600_000).astype("timedelta64[ms]")

    shape = (len(sites), n_hours)
    sun_el, earth_el = np.empty(shape), np.empty(shape)
    sun_az, earth_az = np.empty(shape), np.empty(shape)
    sun_up, earth_up = np.empty(shape, bool), np.empty(shape, bool)
    # Sun and Earth vectors depend only on time: compute them once for all sites.
    to_sun, to_earth = sun_earth_from_moon_centre(_to_jd_tt(times))
    for i, site in enumerate(sites.itertuples()):
        sun_az[i], sun_el[i], sun_dist = _az_el(to_sun, site.lat, site.lon, 0.0)
        earth_az[i], earth_el[i], _ = _az_el(to_earth, site.lat, site.lon, 0.0)
        sun_up[i] = sun_el[i] > -np.degrees(np.arcsin(SUN_RADIUS_KM / sun_dist))
        earth_up[i] = earth_el[i] > 0.0

    return Lookup(
        sites=sites, times=times, sun_el=sun_el, earth_el=earth_el, sun_az=sun_az,
        earth_az=earth_az, sun_up=sun_up, earth_up=earth_up,
        hours_to_sunset=_hours_until_false(sun_up),
        hours_to_earthset=_hours_until_false(earth_up),
        start=start, end=end, max_window_days=max_window_days,
    )


def _index(lookup: Lookup, landing_utc: dt.datetime) -> int:
    t0 = dt.datetime.combine(lookup.start, dt.time(0))
    i = int(round((landing_utc.replace(tzinfo=None) - t0).total_seconds() / 3600 / STEP_HOURS))
    last = int(((lookup.end - lookup.start).days + 1) * 24 / STEP_HOURS)
    if not 0 <= i <= last:
        raise ValueError(f"Landing date must be between {lookup.start} and {lookup.end}.")
    return i


def _longest_false_run(up: np.ndarray) -> np.ndarray:
    """Longest run of False along the last axis, in hours. `up` is (n_sites, n)."""
    best = np.zeros(up.shape[0])
    run = np.zeros(up.shape[0])
    for k in range(up.shape[1]):
        run = np.where(up[:, k], 0.0, run + STEP_HOURS)
        best = np.maximum(best, run)
    return best


def conditions(lookup: Lookup, landing_utc: dt.datetime, window_days: int) -> pd.DataFrame:
    """Conditions at every site for one landing time and mission length.

    One row per site, in the same order as lookup.sites.
    """
    if not 1 <= window_days <= lookup.max_window_days:
        raise ValueError(f"Mission length must be 1 to {lookup.max_window_days} days.")
    i = _index(lookup, landing_utc)
    j = i + int(window_days * 24 / STEP_HOURS)
    sun, earth = lookup.sun_up[:, i:j], lookup.earth_up[:, i:j]

    out = lookup.sites.copy()
    out["sun_el_at_landing"] = lookup.sun_el[:, i]
    out["sun_az_at_landing"] = lookup.sun_az[:, i]
    out["earth_el_at_landing"] = lookup.earth_el[:, i]
    out["earth_az_at_landing"] = lookup.earth_az[:, i]
    out["sun_up_at_landing"] = lookup.sun_up[:, i]
    out["earth_up_at_landing"] = lookup.earth_up[:, i]
    out["hours_to_sunset"] = lookup.hours_to_sunset[:, i]
    out["hours_to_earthset"] = lookup.hours_to_earthset[:, i]
    out["sun_window"] = sun.mean(axis=1)
    out["earth_window"] = earth.mean(axis=1)
    out["longest_dark_h"] = _longest_false_run(sun)
    out["longest_blackout_h"] = _longest_false_run(earth)
    out["max_sun_el_window"] = lookup.sun_el[:, i:j].max(axis=1)
    return out


def rank_for_date(
    lookup: Lookup,
    landing_utc: dt.datetime,
    window_days: int,
    min_sun_long_term: float = 0.5,
    min_earth_long_term: float = 0.5,
    min_sun_window: float = 0.95,
    min_earth_window: float = 0.95,
) -> pd.DataFrame:
    """Apply the limits and rank the sites for a landing date.

    Provisional score: average of the mission-window Sun and Earth ratios
    (flat horizon) and the long-term Sun and Earth ratios (with terrain).
    """
    out = conditions(lookup, landing_utc, window_days)
    reasons = []
    for r in out.itertuples():
        why = []
        if r.sun_long_term < min_sun_long_term:
            why.append("long-term sunlight below limit")
        if r.earth_long_term < min_earth_long_term:
            why.append("long-term Earth visibility below limit")
        if r.sun_window < min_sun_window:
            why.append("mission-window sunlight below limit")
        if r.earth_window < min_earth_window:
            why.append("mission-window Earth contact below limit")
        reasons.append("; ".join(why))
    out["fail_reasons"] = reasons
    out["passes"] = out["fail_reasons"] == ""
    out["score"] = (out["sun_window"] + out["earth_window"] + out["sun_long_term"] + out["earth_long_term"]) / 4
    out = out.sort_values(["passes", "score"], ascending=[False, False]).reset_index(drop=True)
    out["rank"] = out.index + 1
    return out


def timeline(lookup: Lookup, site: str, landing_utc: dt.datetime, window_days: int) -> pd.DataFrame:
    """Hourly Sun and Earth curve at one site over the mission window (for charts)."""
    k = list(lookup.sites["site"]).index(site)
    i = _index(lookup, landing_utc)
    j = i + int(window_days * 24 / STEP_HOURS) + 1
    return pd.DataFrame(
        {
            "time_utc": lookup.times[i:j],
            "sun_el": lookup.sun_el[k, i:j],
            "sun_az": lookup.sun_az[k, i:j],
            "earth_el": lookup.earth_el[k, i:j],
            "earth_az": lookup.earth_az[k, i:j],
            "sun_up": lookup.sun_up[k, i:j],
            "earth_up": lookup.earth_up[k, i:j],
        }
    )


def date_scan(lookup: Lookup, window_days: int, step_days: int = 1) -> pd.DataFrame:
    """Mission-window Sun and Earth ratios for every site and every landing date.

    Long format: date, site, sun_window, earth_window. Use it for a
    site-by-date heat map or to find the best landing dates.
    """
    w = int(window_days * 24 / STEP_HOURS)
    per_day = int(24 / STEP_HOURS)
    n_days = (lookup.end - lookup.start).days + 1
    csun = np.concatenate([np.zeros((len(lookup.sites), 1)), np.cumsum(lookup.sun_up, axis=1)], axis=1)
    cearth = np.concatenate([np.zeros((len(lookup.sites), 1)), np.cumsum(lookup.earth_up, axis=1)], axis=1)
    rows = []
    for d in range(0, n_days, step_days):
        i = d * per_day
        date = lookup.start + dt.timedelta(days=d)
        sun = (csun[:, i + w] - csun[:, i]) / w
        earth = (cearth[:, i + w] - cearth[:, i]) / w
        for k, name in enumerate(lookup.sites["site"]):
            rows.append((date, name, sun[k], earth[k]))
    return pd.DataFrame(rows, columns=["date", "site", "sun_window", "earth_window"])
