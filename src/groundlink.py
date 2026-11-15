"""Earth-side link: which NASA Deep Space Network (DSN) complex can see the Moon, and how often local
rain may degrade a Ka-band link.

Inputs: hourly UTC times (the planner's lookup times) and a site's Earth-visible flags.
Outputs: per-hour Moon elevation at each DSN complex, and mission summaries:
  - x_band: share of the site's Earth-visible hours with at least one complex seeing the Moon
            above a 10 deg antenna mask (X band, about 8.4 GHz, is barely affected by rain);
  - ka_weather: the same share, weighted by the chance that it is dry at a complex in view
            (Ka band, about 32 GHz, loses margin in rain).

Weather is climatology, not a forecast: the monthly share of days with measurable precipitation at a
weather station near each complex. Treating a wet day as a lost Ka link for all its hours is
conservative (it rarely rains all day). Stations are treated as independent.

Moon position: ERFA moon98 (same as ephemeris.py), turned into Earth-fixed coordinates with the
IAU 2006/2000A celestial-to-terrestrial matrix (erfa.c2t06a). Polar motion is ignored (< 1 arcsec).
"""
from __future__ import annotations

import numpy as np
import erfa

AU_M = 149_597_870_700.0
MASK_DEG = 10.0

# Antenna location (approximate, WGS84) and monthly precipitation days (Jan..Dec) at a nearby station.
STATIONS = {
    "Goldstone": dict(lat=35.4267, lon=-116.8900, h=1000.0, country="USA",
                      wet_days=[3.9, 4.2, 2.6, 1.3, 0.8, 0.2, 1.5, 0.9, 0.8, 1.1, 1.6, 3.0],
                      weather_source="Barstow, CA, NOAA 1991-2020 normals, days >= 0.01 in"),
    "Madrid": dict(lat=40.4313, lon=-4.2480, h=830.0, country="Spain",
                   wet_days=[5.4, 5.2, 5.4, 6.8, 6.3, 2.8, 1.4, 1.4, 3.5, 7.1, 6.5, 5.9],
                   weather_source="Madrid Cuatro Vientos, AEMET normals, days >= 1 mm"),
    "Canberra": dict(lat=-35.4014, lon=148.9817, h=690.0, country="Australia",
                     wet_days=[6.8, 6.7, 5.7, 5.4, 6.3, 9.7, 10.0, 8.5, 9.8, 9.1, 10.2, 7.2],
                     weather_source="Canberra Airport, BoM 1991-2010 averages, days >= 0.2 mm"),
}
NAMES = list(STATIONS)
_DAYS_IN_MONTH = np.array([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])


def wet_share() -> np.ndarray:
    """(3, 12) share of days with precipitation, per complex and month."""
    return np.array([np.array(STATIONS[n]["wet_days"]) / _DAYS_IN_MONTH for n in NAMES])


def moon_elevation(times_utc: np.ndarray) -> np.ndarray:
    """(3, T) Moon centre elevation in degrees at each DSN complex, topocentric."""
    t = np.asarray(times_utc, dtype="datetime64[s]").astype("int64") / 86400.0 + 2440587.5
    u1, u2 = np.full_like(t, 2400000.5), t - 2400000.5
    tai1, tai2 = erfa.utctai(u1, u2)
    tt1, tt2 = erfa.taitt(tai1, tai2)
    rc2t = erfa.c2t06a(tt1, tt2, u1, u2, 0.0, 0.0)          # (T, 3, 3)
    moon = erfa.moon98(tt1, tt2)["p"] * AU_M                 # (T, 3) GCRS, metres
    moon_t = np.einsum("tij,tj->ti", rc2t, moon)              # Earth-fixed
    out = []
    for n in NAMES:
        s = STATIONS[n]
        lat, lon = np.radians(s["lat"]), np.radians(s["lon"])
        stn = erfa.gd2gc(1, lon, lat, s["h"])
        up = np.array([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)])
        d = moon_t - stn
        out.append(np.degrees(np.arcsin(d @ up / np.linalg.norm(d, axis=1))))
    return np.array(out)


def link_summary(moon_el: np.ndarray, months: np.ndarray, earth_up: np.ndarray) -> dict:
    """Mission summary for one site. moon_el (3, n), months (n,) 1..12, earth_up (n,) bool."""
    inview = moon_el >= MASK_DEG                              # (3, n)
    p_wet = wet_share()[:, months - 1]                        # (3, n)
    any_view = inview.any(axis=0)
    p_all_wet = np.where(inview, p_wet, 1.0).prod(axis=0)    # complexes not in view count as unavailable
    ka = np.where(any_view, 1.0 - p_all_wet, 0.0)
    e = earth_up.astype(bool)
    n_e = max(int(e.sum()), 1)
    return dict(
        x_band=float((any_view & e).sum() / n_e),
        ka_weather=float(ka[e].sum() / n_e),
        per_station={n: float((inview[k] & e).sum() / n_e) for k, n in enumerate(NAMES)},
        earth_hours=int(e.sum()),
        end_to_end=float((ka * e).sum() / len(e)) if len(e) else 0.0,   # share of all mission hours
    )
