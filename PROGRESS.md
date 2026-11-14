<!-- AI-assisted update by OpenAI Codex, 2026-11-14; physics derivation entries merged with current GitHub progress. -->
# Progress

Deadline: **Sunday 15 November, 23:59** (local time of our Local Event). Aim to submit a first version early; the project can be edited and resubmitted until the deadline.

Status values: `todo`, `doing`, `done`, `blocked`.

## Tasks

| # | Task | Owner | Status | Notes |
|---|---|---|---|---|
| 1 | Agree on concept and scope (sites, date range, factors) | | todo | |
| 2 | Choose 4–6 preset south-pole sites | | todo | |
| 3 | Ephemeris pipeline: Sun and Earth elevation over time for one site (flat horizon) | Claude (for Qiming) | done | `src/ephemeris.py`; checked against JPL Horizons at 10 points, within 0.002° elevation |
| 4 | Terrain horizon for preset sites, precomputed | Claude (for Qiming) | done | `data/terrain_horizons.txt` (13 sites), `data/horizon_calibration.json`. Before calibration: Earth visibility within 0.5 points of NASA at 9 of 13 sites; Sun differs 6.5 points on average, 17 at worst |
| 5 | Metrics per scenario (sunlit %, longest darkness, Earth visible %, longest blackout) | Claude (for Qiming) | done | `src/planner.py`, terrain skyline included; ran for 2027–2030 |
| 6 | Weighted score, ranking and Pareto set | Claude (for Qiming) | doing | Done in `src/planner.py`: five limits, three-factor weighted score, slip stability columns, nearest passing dates, best dates per site, custom coordinates (no terrain), eclipse detection; 8 checks in `tests/test_planner.py` pass. Not done: weight ingredients, Pareto set |
| 7 | App: scenario comparison view and timelines | Claude (for Qiming) | done | `src/app.py`: two-step flow, ranked map, site panel, sky panorama, visibility timeline, custom coordinates. Run locally in headless Chrome with no errors; every control exercised in an automated run. Not deployed |
| 8 | Site × date heatmap (robustness to delay) | Claude (for Qiming) | done | "Compare dates" tab in `src/app.py`; slip worst case shown per site |
| 9 | Demo: 7 slides or 30-second video, in English | | todo | Hard limits |
| 10 | Project page text: summary, description, NASA data, references, AI use | | todo | |
| 11 | Make all links public and test them in a private window | | todo | |
| 12 | Submit for judging | | todo | |

| 13 | Derive physical geometry and coordinate transformations | OpenAI Codex | done | `docs/physics-and-coordinates.md`: 24 projection round trips, cardinal directions, ENU bases, curvature and pixel-centre checks passed; no date-specific NASA-tool comparison. |
| 14 | Audit raw-raster pixel registration and recompute site coordinates if needed | Claude (for Qiming) | done | Confirmed: the first analysis used a half-pixel-shifted transform (+30 m in x, -30 m in y). Site coordinates were recomputed from the raw rasters with NASA's pixel-centre convention, x=(c-2528.5)*60, y=(2528.5-r)*60, and are stored in `data/terrain_horizons.txt`, which the code uses. `data/a3_region_visibility_stats.json` keeps the earlier coordinates (about 42 m off) and is marked as superseded for positions; its visibility values are unaffected. |

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
| 14 Nov | Date-specific results come from a table precomputed once, so date changes are lookups | Team lead: transitions must be smooth |
| 14 Nov | Some factors act as hard limits before scoring | Team lead's choice; default values in `docs/design-principles.md` |

| 14 Nov | Physics derivation records explicit parameters without adopting mission-window, disc-visibility, observer-height or weighting defaults | Documentation scope only; open team decisions remain open |

## References and AI use

List everything here as you use it. The submission form asks for all of it.

### NASA data and resources
- NASA PDS LOLA solar visibility metadata: https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/extras/illumination/img/avgvisib_85s_060m_201608.lbl ; polar projection catalog: https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/catalog/dsmap_polar.cat . Inspected for task 13; raw imagery not downloaded in that task. Earth label fetch unsuccessful; its disc definition remains unverified in this audit.
- NASA PDS LOLA scaling FAQ: https://pds-geosciences.wustl.edu/missions/lro/lola_faq.htm ; JPL Horizons manual: https://ssd.jpl.nasa.gov/horizons/manual.html ; NASA NAIF lunar frame tutorial: https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/Tutorials/pdf/individual_docs/23_lunar-earth_pck-fk.pdf . Consulted for physical and frame conventions; no Horizons ephemeris request executed.
- NASA Cross-Program Design Specification for Natural Environments, revision H, section 3.4.9: https://ntrs.nasa.gov/api/citations/20205007447/downloads/SLS-SPEC-159%20Cross-Program%20Design%20Specification%20for%20Natural%20Environments%20%28DSNE%29%20REVISION%20H.pdf . Physical background on lunar solar day and obliquity, not an adopted project requirement.
- LOLA elevation models LDEM_85S_40M and LDEM_75S_120M (PDS Geosciences Node, https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/): terrain skylines in `data/terrain_horizons.txt`.
- JPL Horizons API (https://ssd.jpl.nasa.gov/api/horizons.api), DE441: reference Sun and Earth azimuth/elevation for two south-pole sites, used to validate `src/ephemeris.py` (`tests/test_ephemeris.py`).
- LOLA average Sun and Earth visibility maps, 60 m/px, south pole (`avgvisib_85s_060m_201608.img`, `..._earth.img`), PDS Geosciences Node: https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/extras/illumination/img/ . Method: Mazarico et al. (2011), Icarus 211, 1066.
- Moon Trek `A3_Named_regions` service (Artemis III region outlines): https://trek.nasa.gov/moon/trekarcgis2/rest/services/A3_Named_regions/MapServer/0

### Partner agency data and other references (data, tools, libraries, images)
- Task 13: existing Python interpreter and standard-library `math`, `ast`, and `pathlib` for analytical checks; OpenAI Codex web search for primary-source documentation. No new runtime dependencies. USGS projection reference and NASA Earth-label retrieval were attempted but unavailable; neither supports a new verified result.
- Python libraries: Streamlit, Plotly, pandas, NumPy, PyERFA (see `requirements.txt`). PyERFA supplies the Earth and Moon position routines `epv00` and `moon98`.
- Moon rotation model: IAU Working Group on Cartographic Coordinates and Rotational Elements, 2009 report (Archinal et al., 2011, Celestial Mechanics and Dynamical Astronomy 109, 101).

### AI tools used and for what
- Claude (Anthropic): reviewed `src/planner.py`; vectorised the date scan (about 20 times faster), accepted late times on the last landing day, and counted eclipses only while the Sun is visible. Three tests added; Astra's `tests/test_interface.py` passes against it.
- Claude (Anthropic): rewrote `src/app.py` as the working interface on top of `src/planner.py`, added `.streamlit/config.toml`, and made the date calendar use the chosen landing hour.
- Claude (Anthropic): rewrote `README.md` to describe the built tool, its data, validation and limits.
- Claude (Anthropic): added slip stability, nearest/best dates, custom coordinates and eclipse detection to `src/planner.py`, and wrote `tests/test_planner.py`.
- Claude (Anthropic): reviewed `docs/physics-and-coordinates.md` against the code, checked its direction vectors numerically against `src/ephemeris.py`, and added its section 10.
- Claude (Anthropic): computed site slopes (`data/site_slopes.json`) from LDEM_85S_40M and added the slope limit and weighted score to `src/planner.py`.
- OpenAI Codex: generated `docs/physics-and-coordinates.md`, derived spherical projection and ENU/terrain visibility geometry, ran analytical checks, and logged a documented half-pixel registration discrepancy. Used the `using-superpowers` and `verification-before-completion` workflow skills. Did not recompute candidate statistics or implement the ephemeris pipeline. The expected challenge reference document was missing from this checkout.
- Claude (Anthropic): computed the terrain skylines (`data/terrain_horizons.txt`) and calibration (`data/horizon_calibration.json`) from the LOLA elevation models, and added terrain to `src/planner.py` and `src/sites.py`.
- Claude (Anthropic): wrote `src/ephemeris.py`, `src/planner.py` and `tests/test_ephemeris.py`. Ran the Horizons comparison and the planner for 2027–2030.
- Claude (Anthropic): wrote the logic module `src/sites.py`, the reference interface `src/app.py` and `docs/ui-interface.md`. The reference interface was run headlessly (both steps, limit sliders, site selection); it has not been viewed in a browser.
- Claude (Anthropic): collected challenge rules and data-source notes (`docs/space-apps-2026-reference.md`); wrote `README.md`, `AGENTS.md`, `PROGRESS.md` and `docs/design-principles.md` from team decisions; computed the visibility statistics in `data/a3_region_visibility_stats.json` from the NASA maps above.
