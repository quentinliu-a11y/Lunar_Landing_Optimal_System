# Interface between the logic and the visual design

AI-assisted document: written by Claude (Anthropic), 2026-11-14.

The work is split in two:

- **Logic** (`src/sites.py`, and later the date calculations): data loading, limits, ranking. 
- **Visual interface**: designed and built separately. It only calls the functions below and never computes results itself.

`src/app.py` is a plain reference interface that shows the agreed flow working. Replace it freely; do not change the logic to fit a design.

## The agreed flow

1. **Date page.** The user picks a planned landing date and time (UTC) and a mission length in days, then continues.
2. **Site page.** A top-down map of the lunar south pole shows the candidate sites, ranked and coloured by whether they pass the limits. The user selects a site and sees its details.

## What the logic provides today

### Python

```python
from sites import load_sites, rank_sites

ranked = rank_sites(load_sites(), min_sun=0.5, min_earth=0.5)   # long-term values only; prefer planner.rank_for_date below
```

### Any other language

```
python src/sites.py 0.5 0.5 > sites.json
```

Both give one record per site:

| Field | Type | Meaning |
|---|---|---|
| `rank` | integer | 1 is best. Sites that fail a limit are ranked after all that pass |
| `site` | text | Artemis III region name |
| `lat`, `lon` | degrees | Latitude (negative = south) and east longitude (negative = west) of the site's best combined spot |
| `x_km`, `y_km` | kilometres | Position on a south polar stereographic map: pole at (0, 0), longitude 0 (towards Earth) along +y, 90°E along +x |
| `sun_long_term` | 0–1 | Share of time the Sun is visible at the surface, 18.6-year average |
| `earth_long_term` | 0–1 | Share of time Earth is visible, 18.6-year average |
| `height_m` | metres | Surface height above the 1737.4 km reference sphere |
| `skyline` | 360 numbers | Terrain skyline elevation in degrees, one per degree of azimuth (clockwise from lunar north) |
| `passes` | true/false | Meets both long-term limits |
| `score` | 0–1 | Provisional: average of the two long-term values. Will be replaced by date-specific scoring |

All values are real NASA LOLA figures; sources are in `data/a3_region_visibility_stats.json`.

## Date-specific conditions (new)

Everything is precomputed once into a lookup table, so changing the date is a table lookup and stays fast enough for sliders and animation.

```python
import datetime as dt
import streamlit as st
import planner

@st.cache_resource            # build once per app start (about 1.5 s for four years)
def get_lookup():
    return planner.build_lookup(dt.date(2027, 1, 1), dt.date(2030, 12, 31))

lookup = get_lookup()
landing = dt.datetime(2028, 1, 1, 0, 0)          # UTC

ranked = planner.rank_for_date(lookup, landing, window_days=14)       # about 20 ms
curve  = planner.timeline(lookup, "Malapert Massif", landing, 14)     # under 1 ms
scan   = planner.date_scan(lookup, window_days=14)                    # about 0.1 s, every site x every date
```

`rank_for_date` returns the fields of the table above plus:

| Field | Type | Meaning |
|---|---|---|
| `sun_window`, `earth_window` | 0–1 | Share of the mission window with the Sun / Earth visible above the terrain skyline |
| `longest_dark_h`, `longest_blackout_h` | hours | Longest unbroken period in the window without Sun / without Earth |
| `hours_to_sunset`, `hours_to_earthset` | hours | Time from landing until the Sun / Earth next sets. 0 means it is already down |
| `sun_el_at_landing`, `earth_el_at_landing` | degrees | Elevation at landing, centre of the disc, relative to a level horizon |
| `sun_margin_at_landing`, `earth_margin_at_landing` | degrees | How far the top edge of the disc is above the terrain skyline. Negative means hidden behind terrain |
| `sun_az_at_landing`, `earth_az_at_landing` | degrees | Direction, clockwise from lunar north |
| `sun_up_at_landing`, `earth_up_at_landing` | true/false | Visible at landing |
| `max_sun_el_window` | degrees | Highest Sun elevation during the window |
| `slope_site_deg`, `slope_mean_deg`, `slope_max_deg` | degrees | Slope at the site, and the mean and maximum within 120 m of it (80 m baseline, LOLA 40 m elevation model) |
| `flatness` | 0–1 | 1 − mean slope ÷ slope limit; 0 when the slope is at or over the limit |
| `passes` | true/false | Meets all five limits (two long-term, two mission-window, slope) |
| `fail_reasons` | text | Which limits failed; empty when the site passes |
| `score` | 0–1 | Weighted average of three factor scores: `sun_window`, `earth_window`, `flatness`. Equal weights by default; provisional |

`timeline` returns hourly rows: `time_utc`, `sun_el`, `sun_az`, `earth_el`, `earth_az`, `sun_margin`, `earth_margin`, `sun_up`, `earth_up`. Use it for the elevation chart and to draw the Sun's and Earth's paths on the panorama.

`planner.skyline(lookup, site)` returns the terrain skyline for the horizon panorama: `azimuth_deg` (0–359), `terrain_el_deg`, and `sun_limit_deg` / `earth_limit_deg`, the calibrated lines the Sun's / Earth's top edge must clear. Draw `terrain_el_deg` as the landscape; a body is visible when its top edge is above its limit line.

`date_scan` returns `date`, `site`, `sun_window`, `earth_window` for a site-by-date heat map.

Limits are arguments of `rank_for_date`: `min_sun_long_term`, `min_earth_long_term` (default 0.5), `min_sun_window`, `min_earth_window` (default 0.95) and `max_slope_deg` (default 10, applied to `slope_mean_deg`).

Weights are the `weights` argument, for example `weights={"sunlight": 2, "earth": 1, "flatness": 1}`. Give the user sliders for the limits and the three weights, and always show the weights in use.

### Must be shown with these values

- **"Estimate anchored to NASA long-term data."** Visibility uses the real terrain skyline from NASA LOLA elevation models, shifted by one constant per site so that our 18.6-year average equals NASA's long-term figure. Near the pole the Sun grazes the skyline, so results for a specific date are estimates.
- "Earth visible" means any part of Earth's disc is above the skyline. A specific ground station may be out of view for part of that time.
- Sun and Earth positions were checked against NASA JPL Horizons and agree within 0.01°.
- Lunar eclipses are not modelled: a site can be shown as sunlit while Earth is blocking the Sun.

## What is not available yet

Do not display numbers for these until the logic supplies them. Show "not available yet" instead.

- Custom coordinates (the logic supports any latitude/longitude through `ephemeris.sky_positions`, but it is not wired into the ranking)

## Rules for the visual interface

- **Geometry must be true.** Use the top-down polar map with the `x_km`, `y_km` positions. At the south pole the Sun and Earth sit within a few degrees of the horizon; never draw Earth high in the sky.
- **No invented numbers** and no decorative gauges with made-up values.
- **English only**, as the competition requires.
- **AI-generated images or video need a visible watermark.** Do not create or alter NASA logos or mission identifiers.
- Show what failed and why for sites that do not pass a limit; do not hide them.
- All 13 Artemis III regions are included. "de Gerlache Rim 2" uses its best spot outside the overlapping "de Gerlache Rim" region.
