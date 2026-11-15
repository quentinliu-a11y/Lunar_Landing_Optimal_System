"""Where the Sun and Earth are in the sky of a site on the Moon.

AI-assisted: written by Claude (Anthropic), 2026-11-14.

Input : site latitude/longitude (degrees, east positive) and UTC times.
Output: azimuth and elevation (degrees) of the Sun's and Earth's centres.
        Azimuth is clockwise from lunar north; elevation is above the plane
        perpendicular to local "up" on a 1737.4 km sphere (a FLAT horizon:
        terrain is not included here).

Method (offline, no internet needed):
- Sun and Earth-Moon geometry from the ERFA routines epv00 and moon98.
- Moon orientation from the IAU (WGCCRE 2009) rotation model.
- The site's own position on the Moon is included (parallax).
- Light travel time and aberration are ignored (effect below 0.01 degrees).

Checked against NASA JPL Horizons (DE441, airless apparent az/el) for two
south-pole sites, Jan-Feb 2028; see tests/test_ephemeris.py for the result.
"""

from __future__ import annotations

import erfa
import numpy as np

MOON_RADIUS_KM = 1737.4
AU_KM = 149_597_870.7
SUN_RADIUS_KM = 695_700.0
EARTH_RADIUS_KM = 6_378.137
_J2000_JD = 2451545.0


def _to_jd_tt(times_utc) -> np.ndarray:
    """UTC datetimes -> Julian date in Terrestrial Time (TT = UTC + 69.184 s)."""
    times = np.atleast_1d(np.asarray(times_utc, dtype="datetime64[ms]"))
    days = (times - np.datetime64("2000-01-01T12:00:00", "ms")) / np.timedelta64(1, "D")
    return _J2000_JD + days + 69.184 / 86400.0


def _rot_z(a):
    c, s = np.cos(a), np.sin(a)
    z, o = np.zeros_like(a), np.ones_like(a)
    return np.stack([np.stack([c, s, z], -1), np.stack([-s, c, z], -1), np.stack([z, z, o], -1)], -2)


def _rot_x(a):
    c, s = np.cos(a), np.sin(a)
    z, o = np.zeros_like(a), np.ones_like(a)
    return np.stack([np.stack([o, z, z], -1), np.stack([z, c, s], -1), np.stack([z, -s, c], -1)], -2)


def moon_orientation(jd_tt: np.ndarray):
    """IAU rotation model of the Moon: pole right ascension, declination and
    prime-meridian angle W, all in radians."""
    d = jd_tt - _J2000_JD
    T = d / 36525.0
    e = np.radians(
        np.stack(
            [
                125.045 - 0.0529921 * d,
                250.089 - 0.1059842 * d,
                260.008 + 13.0120009 * d,
                176.625 + 13.3407154 * d,
                357.529 + 0.9856003 * d,
                311.589 + 26.4057084 * d,
                134.963 + 13.0649930 * d,
                276.617 + 0.3287146 * d,
                34.226 + 1.7484877 * d,
                15.134 - 0.1589763 * d,
                119.743 + 0.0036096 * d,
                239.961 + 0.1643573 * d,
                25.053 + 12.9590088 * d,
            ]
        )
    )
    s, c = np.sin(e), np.cos(e)
    ra = (269.9949 + 0.0031 * T - 3.8787 * s[0] - 0.1204 * s[1] + 0.0700 * s[2]
          - 0.0172 * s[3] + 0.0072 * s[5] - 0.0052 * s[9] + 0.0043 * s[12])
    dec = (66.5392 + 0.0130 * T + 1.5419 * c[0] + 0.0239 * c[1] - 0.0278 * c[2]
           + 0.0068 * c[3] - 0.0029 * c[5] + 0.0009 * c[6] + 0.0008 * c[9] - 0.0009 * c[12])
    w = (38.3213 + 13.17635815 * d - 1.4e-12 * d * d + 3.5610 * s[0] + 0.1208 * s[1]
         - 0.0642 * s[2] + 0.0158 * s[3] + 0.0252 * s[4] - 0.0066 * s[5] - 0.0047 * s[6]
         - 0.0046 * s[7] + 0.0028 * s[8] + 0.0052 * s[9] + 0.0040 * s[10] + 0.0019 * s[11]
         - 0.0044 * s[12])
    return np.radians(ra), np.radians(dec), np.radians(w % 360.0)


def sun_earth_from_moon_centre(jd_tt: np.ndarray):
    """Vectors from the Moon's centre to the Sun and to the Earth, in the
    Moon-fixed frame, kilometres. Shape (n, 3) each."""
    pvh, _ = erfa.epv00(jd_tt, 0.0)          # Earth relative to Sun, au
    moon = erfa.moon98(jd_tt, 0.0)           # Moon relative to Earth, au
    earth_helio = pvh["p"] * AU_KM
    moon_geo = moon["p"] * AU_KM
    to_earth = -moon_geo
    to_sun = -earth_helio - moon_geo

    ra, dec, w = moon_orientation(jd_tt)
    rot = _rot_z(w) @ _rot_x(np.pi / 2 - dec) @ _rot_z(np.pi / 2 + ra)
    return np.einsum("nij,nj->ni", rot, to_sun), np.einsum("nij,nj->ni", rot, to_earth)


def _az_el(vec_from_centre: np.ndarray, lat_deg: float, lon_deg: float, height_km: float):
    lat, lon = np.radians(lat_deg), np.radians(lon_deg)
    up = np.array([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)])
    site = (MOON_RADIUS_KM + height_km) * up
    pole = np.array([0.0, 0.0, 1.0])
    north = pole - np.dot(pole, up) * up
    north /= np.linalg.norm(north)
    east = np.cross(north, up)

    d = vec_from_centre - site
    dist = np.linalg.norm(d, axis=1)
    d = d / dist[:, None]
    el = np.degrees(np.arcsin(np.clip(d @ up, -1, 1)))
    az = np.degrees(np.arctan2(d @ east, d @ north)) % 360.0
    return az, el, dist


def sky_positions(lat_deg: float, lon_deg: float, times_utc, height_km: float = 0.0) -> dict:
    """Sun and Earth azimuth/elevation at a lunar site for the given UTC times.

    Returns a dict of numpy arrays: sun_az, sun_el, earth_az, earth_el
    (degrees, body centres) and sun_radius_deg, earth_radius_deg (apparent
    angular radius of each disc).
    """
    jd = _to_jd_tt(times_utc)
    to_sun, to_earth = sun_earth_from_moon_centre(jd)
    sun_az, sun_el, sun_dist = _az_el(to_sun, lat_deg, lon_deg, height_km)
    earth_az, earth_el, earth_dist = _az_el(to_earth, lat_deg, lon_deg, height_km)
    return {
        "sun_az": sun_az,
        "sun_el": sun_el,
        "earth_az": earth_az,
        "earth_el": earth_el,
        "sun_radius_deg": np.degrees(np.arcsin(SUN_RADIUS_KM / sun_dist)),
        "earth_radius_deg": np.degrees(np.arcsin(EARTH_RADIUS_KM / earth_dist)),
    }

