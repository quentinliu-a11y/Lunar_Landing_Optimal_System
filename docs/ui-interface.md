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

ranked = rank_sites(load_sites(), min_sun=0.5, min_earth=0.5)   # pandas DataFrame, best first
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
| `region_best_sun`, `region_best_earth` | 0–1 | Highest value found anywhere inside the region (may be at a different spot) |
| `passes` | true/false | Meets both long-term limits |
| `score` | 0–1 | Provisional: average of the two long-term values. Will be replaced by date-specific scoring |

All values are real NASA LOLA figures; sources are in `data/a3_region_visibility_stats.json`.

## What is not available yet

Do not display numbers for these until the logic supplies them. Show "not available yet" instead.

- Sun and Earth elevation and direction at a site for the chosen date
- Time remaining until sunset and Earthset
- Sunlight and Earth-contact ratios over the mission window
- Terrain horizon profile for the panorama view
- Slope

The chosen date and mission length are collected now but do not change the ranking yet.

## Rules for the visual interface

- **Geometry must be true.** Use the top-down polar map with the `x_km`, `y_km` positions. At the south pole the Sun and Earth sit within a few degrees of the horizon; never draw Earth high in the sky.
- **No invented numbers** and no decorative gauges with made-up values.
- **English only**, as the competition requires.
- **AI-generated images or video need a visible watermark.** Do not create or alter NASA logos or mission identifiers.
- Show what failed and why for sites that do not pass a limit; do not hide them.
- Known quirk: "de Gerlache Rim" and "de Gerlache Rim 2" overlap and currently share the same best spot, so their markers coincide.
- Two Artemis III regions (Amundsen Rim, Nobile Rim 2) are missing because they lie outside the data analysed so far.
