"""Terrain skyline for any point near the lunar south pole, from a NASA LOLA elevation grid.

AI-assisted: written by Claude (Anthropic) on 2026-11-15.

Data: data/lola_spole_500m.npz, a 1200 x 1200 grid of surface heights (int16, metres above the
1,737.4 km sphere) covering x, y = -300 ... +300 km in the Moon2000 south polar stereographic projection
(500 m pixels, row 0 = y +300 km, column 0 = x -300 km). Exported on 15 Nov 2026 from the NASA Moon Trek
image service LRO_LOLA_DEM_SPole45_100mp_v04 (LOLA, 100 m/pixel source, bilinear resampling to 500 m):
https://trek.nasa.gov/moon/trekarcgis/rest/services/LRO_LOLA_DEM_SPole45_100mp_v04/ImageServer

Projection (same as sites.latlon_to_polar_xy_km): rho = 2 R tan((90 deg + lat) / 2),
x = rho sin(lon), y = rho cos(lon), lon east-positive.

Skyline: for each azimuth (clockwise from lunar north; near the south pole north points away from the pole),
the highest elevation angle of terrain seen from 2 m above the surface, searching out to 150 km or the edge of
the grid, on a spherical Moon (no refraction). This is coarser than the 40 m / 120 m skylines of the 13 named
sites (data/terrain_horizons.txt) and is not calibrated against NASA's long-term visibility maps.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np

R_M = 1_737_400.0
HALF_M = 300_000.0
PIX_M = 500.0
OBS_HEIGHT_M = 2.0
MAX_DIST_M = 150_000.0
# Terrain closer than this is skipped: at 500 m pixels it mostly echoes the observer's own (smoothed) hill.
# Chosen by comparing with the 13 high-resolution site skylines: mean bias -0.25 deg, mean RMS 0.83 deg
# (vs +0.46 / 1.25 deg when starting at 250 m).
NEAR_START_M = 750.0
DATA = Path(__file__).resolve().parent.parent / "data" / "lola_spole_500m.npz"


@lru_cache(maxsize=1)
def grid() -> np.ndarray:
    return np.load(DATA)["height_m"].astype(np.float32)


def xy_m(lat_deg: float, lon_deg: float) -> tuple[float, float]:
    rho = 2.0 * R_M * np.tan(np.radians(90.0 + lat_deg) / 2.0)
    lon = np.radians(lon_deg)
    return float(rho * np.sin(lon)), float(rho * np.cos(lon))


def covered(lat_deg: float, lon_deg: float, margin_m: float = 20_000.0) -> bool:
    """True when the point lies inside the grid with some room for the horizon search."""
    x, y = xy_m(lat_deg, lon_deg)
    return lat_deg < 0 and max(abs(x), abs(y)) <= HALF_M - margin_m


def height_at(x, y) -> np.ndarray:
    """Bilinear surface height (m) at map coordinates (m); NaN outside the grid."""
    g = grid()
    n = g.shape[0]
    col = (np.asarray(x) + HALF_M) / PIX_M - 0.5
    row = (HALF_M - np.asarray(y)) / PIX_M - 0.5
    inside = (col >= 0) & (col <= n - 1.001) & (row >= 0) & (row <= n - 1.001)
    c0 = np.clip(np.floor(col).astype(int), 0, n - 2)
    r0 = np.clip(np.floor(row).astype(int), 0, n - 2)
    fc, fr = col - c0, row - r0
    h = (g[r0, c0] * (1 - fc) * (1 - fr) + g[r0, c0 + 1] * fc * (1 - fr)
         + g[r0 + 1, c0] * (1 - fc) * fr + g[r0 + 1, c0 + 1] * fc * fr)
    return np.where(inside, h, np.nan)


def skyline(lat_deg: float, lon_deg: float) -> tuple[np.ndarray, float]:
    """(360 skyline elevation angles in degrees, surface height in m) for a point."""
    x0, y0 = xy_m(lat_deg, lon_deg)
    h0 = float(height_at(x0, y0)) + OBS_HEIGHT_M
    lon = np.radians(lon_deg)
    north = np.array([np.sin(lon), np.cos(lon)])        # away from the pole
    east = np.array([np.cos(lon), -np.sin(lon)])
    az = np.radians(np.arange(360.0))
    dirs = np.cos(az)[:, None] * north + np.sin(az)[:, None] * east     # (360, 2)
    d = np.concatenate([np.arange(NEAR_START_M, 25_000.0, 250.0), np.arange(25_000.0, MAX_DIST_M + 1, 500.0)])
    px = x0 + dirs[:, 0:1] * d                                         # (360, n)
    py = y0 + dirs[:, 1:2] * d
    ht = height_at(px, py)
    gamma = d / R_M                                                    # central angle
    rt, ro = R_M + ht, R_M + h0
    elev = np.degrees(np.arctan2(rt * np.cos(gamma) - ro, rt * np.sin(gamma)))
    sky = np.nanmax(np.where(np.isnan(elev), -90.0, elev), axis=1)
    # A level sphere's horizon dip from the observer's height, where terrain is lower than that.
    dip = -np.degrees(np.arccos(R_M / ro)) if ro > R_M else 0.0
    return np.maximum(sky, dip), h0 - OBS_HEIGHT_M
