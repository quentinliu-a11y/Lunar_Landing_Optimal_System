"""Checks the offline Sun/Earth positions against NASA JPL Horizons.

AI-assisted: written by Claude (Anthropic), 2026-11-14.

Reference values were fetched on 2026-11-14 from the JPL Horizons API
(DE441, observer on the Moon, airless apparent azimuth/elevation, QUANTITIES=4,
CENTER='coord@301', geodetic site at 0 km altitude).

Result when last run: all 10 points agree within 0.002 deg in elevation and
0.008 deg in azimuth.

Run:  python tests/test_ephemeris.py
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from ephemeris import sky_positions  # noqa: E402

# lat, east lon, body, UTC, Horizons azimuth, Horizons elevation
REFERENCE = [
    (-89.315, 245.953, "sun", "2028-01-01T00:00", 247.269, 0.365),
    (-89.315, 245.953, "sun", "2028-01-21T00:00", 4.358, 0.701),
    (-89.315, 245.953, "sun", "2028-02-06T00:00", 169.505, -1.030),
    (-89.315, 245.953, "earth", "2028-01-01T00:00", 112.912, 2.159),
    (-89.315, 245.953, "earth", "2028-01-19T00:00", 120.847, -7.436),
    (-89.315, 245.953, "earth", "2028-02-03T00:00", 106.902, 6.388),
    (-85.954, 356.609, "sun", "2028-01-12T00:00", 2.994, 4.371),
    (-85.954, 356.609, "sun", "2028-01-27T00:00", 180.595, -4.174),
    (-85.954, 356.609, "earth", "2028-01-06T12:00", 356.288, 10.616),
    (-85.954, 356.609, "earth", "2028-01-19T00:00", 10.202, -3.104),
]


def test_matches_horizons(tol_el=0.01, tol_az=0.02):
    worst_el = worst_az = 0.0
    for lat, lon, body, utc, az_ref, el_ref in REFERENCE:
        sky = sky_positions(lat, lon, [np.datetime64(utc)])
        d_el = abs(sky[f"{body}_el"][0] - el_ref)
        d_az = abs((sky[f"{body}_az"][0] - az_ref + 180) % 360 - 180)
        worst_el, worst_az = max(worst_el, d_el), max(worst_az, d_az)
        assert d_el < tol_el, (body, utc, d_el)
        assert d_az < tol_az, (body, utc, d_az)
    return worst_el, worst_az


if __name__ == "__main__":
    el, az = test_matches_horizons()
    print(f"OK: worst elevation error {el:.4f} deg, worst azimuth error {az:.4f} deg")
