"""Date-specific conditions and ranking for the candidate landing sites.

AI-assisted: written by Claude (Anthropic), 2026-11-14.

Design for speed (so date sliders and animations stay smooth):
- build_lookup() does the heavy work ONCE: an hourly Sun/Earth timeline for
  every site over the whole date range, then per-day mission-window results.
- After that, conditions for any landing date are a table lookup, and the
  hourly curve for a chart is a slice of an array. Nothing is recomputed
  when the user moves the date.

Visibility uses the real terrain skyline of each site (NASA LOLA elevation
models, 40 m and 120 m per pixel), seen from 2 m above the surface:

- Sun visible   : any part of the Sun's disc above the skyline in the Sun's direction.
- Earth visible : any part of Earth's disc above the skyline in Earth's direction.
  (Same definitions as the NASA LOLA long-term visibility maps.)

Calibration: each site's skyline is shifted by one constant per body
(data/horizon_calibration.json) so that our 18.6-year average equals the NASA
LOLA long-term value at that site. Before calibration our Earth visibility
agrees with NASA within 0.5 percentage points at 9 of 13 sites; Sun visibility
differs by 6.5 points on average (up to 17), because near the pole the Sun
grazes the skyline and tens of metres of position or terrain change the result.
Treat date results as estimates anchored to NASA's long-term figures.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import numpy as np
import pandas as pd

from ephemeris import EARTH_RADIUS_KM, SUN_RADIUS_KM, _az_el, _to_jd_tt, sun_earth_from_moon_centre
from sites import MAST_HEIGHT_M, load_sites

STEP_HOURS = 1.0


@dataclass
class Lookup:
    sites: pd.DataFrame          # one row per site (from sites.load_sites)
    times: np.ndarray            # hourly UTC times, datetime64[ms], length T
    sun_el: np.ndarray           # (n_sites, T) degrees, Sun centre
    earth_el: np.ndarray         # (n_sites, T) degrees, Earth centre
    sun_az: np.ndarray           # (n_sites, T) degrees
    earth_az: np.ndarray         # (n_sites, T) degrees
    sun_margin: np.ndarray       # (n_sites, T) degrees the Sun's top edge is above the skyline (negative = hidden)
    earth_margin: np.ndarray     # (n_sites, T) same for Earth
    sun_up: np.ndarray           # (n_sites, T) bool
    earth_up: np.ndarray         # (n_sites, T) bool
    eclipse: np.ndarray          # (n_sites, T) 0 = none, 1 = Earth covers part of the visible Sun, 2 = all of it
    cum_sun: np.ndarray          # (n_sites, T+1) running count of sunlit hours, for O(1) window ratios
    cum_earth: np.ndarray        # (n_sites, T+1) same for Earth
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
    sun_margin, earth_margin = np.empty(shape), np.empty(shape)
    eclipse = np.zeros(shape, np.int8)
    # Sun and Earth vectors depend only on time: compute them once for all sites.
    to_sun, to_earth = sun_earth_from_moon_centre(_to_jd_tt(times))
    az_grid = np.arange(361.0)
    for i, site in enumerate(sites.itertuples()):
        height_km = (site.height_m + MAST_HEIGHT_M) / 1000.0
        sun_az[i], sun_el[i], sun_dist = _az_el(to_sun, site.lat, site.lon, height_km)
        earth_az[i], earth_el[i], earth_dist = _az_el(to_earth, site.lat, site.lon, height_km)
        sky = np.append(site.skyline, site.skyline[0])
        sun_radius = np.degrees(np.arcsin(SUN_RADIUS_KM / sun_dist))
        earth_radius = np.degrees(np.arcsin(EARTH_RADIUS_KM / earth_dist))
        # Margin = how far the top edge of the disc is above the (calibrated) skyline.
        sun_margin[i] = sun_el[i] + sun_radius - (np.interp(sun_az[i], az_grid, sky) + site.sun_offset_deg)
        earth_margin[i] = earth_el[i] + earth_radius - (np.interp(earth_az[i], az_grid, sky) + site.earth_offset_deg)
        sun_up[i] = sun_margin[i] > 0.0
        earth_up[i] = earth_margin[i] > 0.0
        # Lunar eclipse seen from the site: Earth's disc overlapping the Sun's disc.
        e1, e2 = np.radians(sun_el[i]), np.radians(earth_el[i])
        cos_sep = np.sin(e1) * np.sin(e2) + np.cos(e1) * np.cos(e2) * np.cos(np.radians(sun_az[i] - earth_az[i]))
        sep = np.degrees(np.arccos(np.clip(cos_sep, -1, 1)))
        eclipse[i] = np.where(sep < earth_radius - sun_radius, 2, np.where(sep < earth_radius + sun_radius, 1, 0))
        eclipse[i][~sun_up[i]] = 0  # only matters while the Sun is above the skyline

    return Lookup(
        sites=sites, times=times, sun_el=sun_el, earth_el=earth_el, sun_az=sun_az,
        earth_az=earth_az, sun_margin=sun_margin, earth_margin=earth_margin,
        sun_up=sun_up, earth_up=earth_up, eclipse=eclipse,
        cum_sun=np.concatenate([np.zeros((len(sites), 1)), np.cumsum(sun_up, axis=1)], axis=1),
        cum_earth=np.concatenate([np.zeros((len(sites), 1)), np.cumsum(earth_up, axis=1)], axis=1),
        hours_to_sunset=_hours_until_false(sun_up),
        hours_to_earthset=_hours_until_false(earth_up),
        start=start, end=end, max_window_days=max_window_days,
    )


def _index(lookup: Lookup, landing_utc: dt.datetime) -> int:
    """Index of the hourly sample nearest to the landing time.

    Any time on a day from lookup.start to lookup.end is accepted. A time late
    on the last day that would round into the next day uses that day's last hour.
    """
    t0 = dt.datetime.combine(lookup.start, dt.time(0))
    hours = (landing_utc.replace(tzinfo=None) - t0).total_seconds() / 3600 / STEP_HOURS
    last = int(((lookup.end - lookup.start).days + 1) * 24 / STEP_HOURS)  # first hour after the last day
    if not 0 <= hours < last:
        raise ValueError(f"Landing date must be between {lookup.start} and {lookup.end}.")
    return min(int(round(hours)), last - 1)


def _longest_false_run(up: np.ndarray) -> np.ndarray:
    """Longest run of False along the last axis, in hours. `up` is (n_sites, n)."""
    best = np.zeros(up.shape[0])
    run = np.zeros(up.shape[0])
    for k in range(up.shape[1]):
        run = np.where(up[:, k], 0.0, run + STEP_HOURS)
        best = np.maximum(best, run)
    return best


def conditions(lookup: Lookup, landing_utc: dt.datetime, window_days: int, slip_days: int = 14) -> pd.DataFrame:
    """Conditions at every site for one landing time and mission length.

    One row per site, in the same order as lookup.sites. `slip_days` sets how
    far the landing may move (earlier or later, whole days) for the
    worst-case columns.
    """
    if not 1 <= window_days <= lookup.max_window_days:
        raise ValueError(f"Mission length must be 1 to {lookup.max_window_days} days.")
    i = _index(lookup, landing_utc)
    j = i + int(window_days * 24 / STEP_HOURS)
    sun, earth = lookup.sun_up[:, i:j], lookup.earth_up[:, i:j]

    out = lookup.sites.drop(columns=["skyline"]).copy()
    out["sun_el_at_landing"] = lookup.sun_el[:, i]
    out["sun_az_at_landing"] = lookup.sun_az[:, i]
    out["earth_el_at_landing"] = lookup.earth_el[:, i]
    out["earth_az_at_landing"] = lookup.earth_az[:, i]
    out["sun_margin_at_landing"] = lookup.sun_margin[:, i]
    out["earth_margin_at_landing"] = lookup.earth_margin[:, i]
    out["sun_up_at_landing"] = lookup.sun_up[:, i]
    out["earth_up_at_landing"] = lookup.earth_up[:, i]
    out["hours_to_sunset"] = lookup.hours_to_sunset[:, i]
    out["hours_to_earthset"] = lookup.hours_to_earthset[:, i]
    out["sun_window"] = sun.mean(axis=1)
    out["earth_window"] = earth.mean(axis=1)
    out["longest_dark_h"] = _longest_false_run(sun)
    out["longest_blackout_h"] = _longest_false_run(earth)
    out["max_sun_el_window"] = lookup.sun_el[:, i:j].max(axis=1)
    out["eclipse_hours"] = (lookup.eclipse[:, i:j] > 0).sum(axis=1) * STEP_HOURS

    # Stability if the landing slips: the same window started up to slip_days earlier or later.
    w = j - i
    per_day = int(24 / STEP_HOURS)
    last_start = lookup.cum_sun.shape[1] - 1 - w
    starts = i + per_day * np.arange(-slip_days, slip_days + 1)
    starts = starts[(starts >= 0) & (starts <= last_start)]
    sun_slip = (lookup.cum_sun[:, starts + w] - lookup.cum_sun[:, starts]) / w
    earth_slip = (lookup.cum_earth[:, starts + w] - lookup.cum_earth[:, starts]) / w
    out["sun_window_worst"] = sun_slip.min(axis=1)
    out["earth_window_worst"] = earth_slip.min(axis=1)
    out["slip_dates_checked"] = starts.size  # 2 * slip_days + 1 unless cut short at the edge of the date range
    return out


DEFAULT_WEIGHTS = {"sunlight": 1.0, "earth": 1.0, "flatness": 1.0}


def rank_for_date(
    lookup: Lookup,
    landing_utc: dt.datetime,
    window_days: int,
    min_sun_long_term: float = 0.5,
    min_earth_long_term: float = 0.5,
    min_sun_window: float = 0.95,
    min_earth_window: float = 0.95,
    max_slope_deg: float = 10.0,
    weights: dict | None = None,
    slip_days: int = 14,
) -> pd.DataFrame:
    """Apply the limits and rank the sites for a landing date.

    Limits (a site failing any of them is listed after all passing sites):
    long-term Sun and Earth visibility, mission-window Sun and Earth
    visibility, and mean slope within 120 m of the site.

    Score (0-1) = weighted average of three factor scores, each 0-1:
      sunlight = mission-window Sun ratio
      earth    = mission-window Earth ratio
      flatness = 1 - mean slope / max_slope_deg (0 when the slope is at or over the limit)
    `weights` maps "sunlight", "earth", "flatness" to non-negative numbers;
    equal weights by default. The weighting scheme is provisional.

    Stability columns (not part of the score): sun_window_worst and
    earth_window_worst are the lowest window ratios if the landing moves by up
    to `slip_days` days either way; stable is True when the site would still
    meet the two mission-window limits in that worst case.
    """
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    total = sum(w.values())
    if total <= 0 or min(w.values()) < 0:
        raise ValueError("Weights must be non-negative and not all zero.")

    out = conditions(lookup, landing_utc, window_days, slip_days)
    out["stable"] = (out["sun_window_worst"] >= min_sun_window) & (out["earth_window_worst"] >= min_earth_window)
    out["flatness"] = (1.0 - out["slope_mean_deg"] / max_slope_deg).clip(lower=0.0)
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
        if r.slope_mean_deg > max_slope_deg:
            why.append("slope above limit")
        reasons.append("; ".join(why))
    out["fail_reasons"] = reasons
    out["passes"] = out["fail_reasons"] == ""
    out["score"] = (
        w["sunlight"] * out["sun_window"] + w["earth"] * out["earth_window"] + w["flatness"] * out["flatness"]
    ) / total
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
            "sun_margin": lookup.sun_margin[k, i:j],
            "earth_margin": lookup.earth_margin[k, i:j],
            "sun_up": lookup.sun_up[k, i:j],
            "earth_up": lookup.earth_up[k, i:j],
            "eclipse": lookup.eclipse[k, i:j],
        }
    )


def skyline(lookup: Lookup, site: str) -> pd.DataFrame:
    """Terrain skyline of a site for the panorama view.

    azimuth_deg 0..359 (clockwise from lunar north), terrain_el_deg as computed
    from the elevation model, plus sun_limit_deg / earth_limit_deg: the
    calibrated lines the Sun's / Earth's top edge must clear to be visible.
    """
    row = lookup.sites[lookup.sites["site"] == site].iloc[0]
    return pd.DataFrame(
        {
            "azimuth_deg": np.arange(360),
            "terrain_el_deg": row.skyline,
            "sun_limit_deg": row.skyline + row.sun_offset_deg,
            "earth_limit_deg": row.skyline + row.earth_offset_deg,
        }
    )


def date_scan(lookup: Lookup, window_days: int, step_days: int = 1, hour_utc: int = 0) -> pd.DataFrame:
    """Mission-window Sun and Earth ratios for every site and every landing date.

    Landing is at `hour_utc` o'clock UTC on each date.

    Long format: date, site, sun_window, earth_window. Use it for a
    site-by-date heat map or to find the best landing dates.
    """
    w = int(window_days * 24 / STEP_HOURS)
    per_day = int(24 / STEP_HOURS)
    n_days = (lookup.end - lookup.start).days + 1
    days = np.arange(0, n_days, step_days)
    starts = days * per_day + int(hour_utc / STEP_HOURS)
    sun = (lookup.cum_sun[:, starts + w] - lookup.cum_sun[:, starts]) / w          # (n_sites, n_dates)
    earth = (lookup.cum_earth[:, starts + w] - lookup.cum_earth[:, starts]) / w
    names = lookup.sites["site"].to_numpy()
    dates = [lookup.start + dt.timedelta(days=int(d)) for d in days]
    return pd.DataFrame({
        "date": np.repeat(np.array(dates, dtype=object), len(names)),
        "site": np.tile(names, len(dates)),
        "sun_window": sun.T.ravel(),
        "earth_window": earth.T.ravel(),
    })


def passing_calendar(
    lookup: Lookup,
    window_days: int,
    min_sun_long_term: float = 0.5,
    min_earth_long_term: float = 0.5,
    min_sun_window: float = 0.95,
    min_earth_window: float = 0.95,
    max_slope_deg: float = 10.0,
    hour_utc: int = 0,
) -> pd.DataFrame:
    """Which sites pass all limits on which landing dates (landing at `hour_utc` UTC).

    Long format: date, site, sun_window, earth_window, passes.
    """
    scan = date_scan(lookup, window_days, hour_utc=hour_utc)
    fixed_ok = (
        (lookup.sites["sun_long_term"] >= min_sun_long_term)
        & (lookup.sites["earth_long_term"] >= min_earth_long_term)
        & (lookup.sites["slope_mean_deg"] <= max_slope_deg)
    )
    ok_by_site = dict(zip(lookup.sites["site"], fixed_ok))
    scan["passes"] = (
        (scan["sun_window"] >= min_sun_window) & (scan["earth_window"] >= min_earth_window) & scan["site"].map(ok_by_site)
    )
    return scan


def nearest_passing_dates(lookup: Lookup, landing_utc: dt.datetime, window_days: int, **limits) -> pd.DataFrame:
    """For each site, the closest landing dates that pass all limits.

    Columns: site, passes_on_date, previous_date, next_date, days_to_nearest.
    Dates are None when the site never passes in that direction within the
    lookup range. Use it when few or no sites pass on the chosen date.
    """
    limits.setdefault("hour_utc", landing_utc.hour)  # same time of day as the chosen landing
    cal = passing_calendar(lookup, window_days, **limits)
    day = landing_utc.date()
    rows = []
    for site, grp in cal.groupby("site", sort=False):
        good = grp.loc[grp["passes"], "date"].to_numpy()
        before, after = good[good < day], good[good > day]
        on = bool((good == day).any())
        prev_d = before.max() if before.size else None
        next_d = after.min() if after.size else None
        gaps = [abs((d - day).days) for d in (prev_d, next_d) if d is not None]
        rows.append((site, on, prev_d, next_d, 0 if on else (min(gaps) if gaps else None)))
    return pd.DataFrame(rows, columns=["site", "passes_on_date", "previous_date", "next_date", "days_to_nearest"])


def best_dates(lookup: Lookup, site: str, window_days: int, top: int = 5) -> pd.DataFrame:
    """The landing dates with the best combined window ratios at one site.

    Ranked by the lower of the Sun and Earth window ratios, then by their sum.
    Consecutive days are similar, so results are at least 7 days apart.
    """
    scan = date_scan(lookup, window_days)
    g = scan[scan["site"] == site].copy()
    g["worst_of_two"] = g[["sun_window", "earth_window"]].min(axis=1)
    g["sum"] = g["sun_window"] + g["earth_window"]
    g = g.sort_values(["worst_of_two", "sum"], ascending=False)
    picked = []
    for row in g.itertuples():
        if all(abs((row.date - p.date).days) >= 7 for p in picked):
            picked.append(row)
        if len(picked) == top:
            break
    return pd.DataFrame([(p.date, p.sun_window, p.earth_window) for p in picked], columns=["date", "sun_window", "earth_window"])


def custom_site(lat_deg: float, lon_deg: float, landing_utc: dt.datetime, window_days: int, height_m: float = 0.0):
    """Conditions at any latitude/longitude, WITHOUT terrain.

    The horizon is that of a smooth sphere, so results are an optimistic
    approximation: label them "flat-horizon estimate, terrain not included".
    Returns (summary dict, hourly timeline DataFrame).
    """
    if not -90.0 <= lat_deg <= 90.0:
        raise ValueError("Latitude must be between -90 and 90 degrees.")
    n = int(window_days * 24 / STEP_HOURS)
    t0 = np.datetime64(landing_utc.replace(tzinfo=None), "ms")
    times = t0 + (np.arange(n + 1) * STEP_HOURS * 3_600_000).astype("timedelta64[ms]")
    to_sun, to_earth = sun_earth_from_moon_centre(_to_jd_tt(times))
    height_km = (height_m + MAST_HEIGHT_M) / 1000.0
    sun_az, sun_el, sun_dist = _az_el(to_sun, lat_deg, lon_deg, height_km)
    earth_az, earth_el, earth_dist = _az_el(to_earth, lat_deg, lon_deg, height_km)
    sun_up = sun_el + np.degrees(np.arcsin(SUN_RADIUS_KM / sun_dist)) > 0.0
    earth_up = earth_el + np.degrees(np.arcsin(EARTH_RADIUS_KM / earth_dist)) > 0.0
    tl = pd.DataFrame(
        {"time_utc": times, "sun_el": sun_el, "sun_az": sun_az, "earth_el": earth_el, "earth_az": earth_az,
         "sun_up": sun_up, "earth_up": earth_up}
    )

    def first_false(up):
        idx = np.flatnonzero(~up)
        return float(idx[0] * STEP_HOURS) if idx.size else None  # None = stays up for the whole window

    summary = {
        "lat": lat_deg, "lon": lon_deg, "terrain_included": False,
        "sun_window": float(sun_up[:n].mean()), "earth_window": float(earth_up[:n].mean()),
        "longest_dark_h": float(_longest_false_run(sun_up[None, :n])[0]),
        "longest_blackout_h": float(_longest_false_run(earth_up[None, :n])[0]),
        "hours_to_sunset": first_false(sun_up), "hours_to_earthset": first_false(earth_up),
        "sun_el_at_landing": float(sun_el[0]), "earth_el_at_landing": float(earth_el[0]),
        "sun_az_at_landing": float(sun_az[0]), "earth_az_at_landing": float(earth_az[0]),
        "max_sun_el_window": float(sun_el[:n].max()),
    }
    return summary, tl
