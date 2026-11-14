# Progress

Deadline: **Sunday 15 November, 23:59** (local time of our Local Event). Aim to submit a first version early; the project can be edited and resubmitted until the deadline.

Status values: `todo`, `doing`, `done`, `blocked`.

## Tasks

| # | Task | Owner | Status | Notes |
|---|---|---|---|---|
| 1 | Agree on concept and scope (sites, date range, factors) | | todo | |
| 2 | Choose 4–6 preset south-pole sites | | todo | |
| 3 | Ephemeris pipeline: Sun and Earth elevation over time for one site (flat horizon) | | todo | JPL Horizons |
| 4 | Terrain horizon for preset sites, precomputed | | todo | LOLA topography |
| 5 | Metrics per scenario (sunlit %, longest darkness, Earth visible %, longest blackout) | | todo | |
| 6 | Weighted score, ranking and Pareto set | | todo | |
| 7 | App: scenario comparison view and timelines | | todo | |
| 8 | Site × date heatmap (robustness to delay) | | todo | |
| 9 | Demo: 7 slides or 30-second video, in English | | todo | Hard limits |
| 10 | Project page text: summary, description, NASA data, references, AI use | | todo | |
| 11 | Make all links public and test them in a private window | | todo | |
| 12 | Submit for judging | | todo | |

## Proposed split for three people

Not agreed yet. Each role hands over through files in `data/`, so the three can work in parallel.

| Role | Owns | Tasks | Hands over |
|---|---|---|---|
| A. Data and physics | Sun and Earth positions, terrain horizon, per-site timelines | 3, 4 | One timeline file per site: time, Sun elevation, Earth elevation, sunlit yes/no, Earth visible yes/no |
| B. Scoring and validation | Site list, limits, weights, stability, ranking, checks against QuickMap | 2, 5, 6 | A ranking function: (date, settings) -> table of sites with factor values, pass/fail and score |
| C. Interface and presentation | App pages, map, panorama, demo, submission text | 7, 8, 9, 10 | The running app, the demo and the project page text |

Tasks 1, 11 and 12 are shared. First step for everyone: agree the file formats above, and B gives C a small made-up sample so the interface can be built before real data exists.

## Decisions

| Date | Decision | Why |
|---|---|---|
| 14 Nov | Tool is date-first: pick a landing date, see conditions, go to a map of recommended sites | Team lead's concept |
| 14 Nov | Rank a fixed list of named sites instead of scoring every pixel | Achievable by the deadline; scores are explainable |
| 14 Nov | Top three factors: sunlight ratio, Earth communication availability, flatness | Team lead's choice |
| 14 Nov | Logic code and visual interface are built separately; the interface only calls the logic (`docs/ui-interface.md`) | Team lead's choice |
| 14 Nov | Some factors act as hard limits before scoring | Team lead's choice; default values in `docs/design-principles.md` |

## References and AI use

List everything here as you use it. The submission form asks for all of it.

### NASA data and resources
- LOLA average Sun and Earth visibility maps, 60 m/px, south pole (`avgvisib_85s_060m_201608.img`, `..._earth.img`), PDS Geosciences Node: https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/extras/illumination/img/ . Method: Mazarico et al. (2011), Icarus 211, 1066.
- Moon Trek `A3_Named_regions` service (Artemis III region outlines): https://trek.nasa.gov/moon/trekarcgis2/rest/services/A3_Named_regions/MapServer/0

### Partner agency data and other references (data, tools, libraries, images)
- Python libraries: Streamlit, Plotly, pandas (see `requirements.txt`).

### AI tools used and for what
- Claude (Anthropic): wrote the logic module `src/sites.py`, the reference interface `src/app.py` and `docs/ui-interface.md`. The reference interface was run headlessly (both steps, limit sliders, site selection); it has not been viewed in a browser.
- Claude (Anthropic): collected challenge rules and data-source notes (`docs/space-apps-2026-reference.md`); wrote `README.md`, `AGENTS.md`, `PROGRESS.md` and `docs/design-principles.md` from team decisions; computed the visibility statistics in `data/a3_region_visibility_stats.json` from the NASA maps above.
