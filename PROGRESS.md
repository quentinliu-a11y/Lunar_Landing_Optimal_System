<!-- AI-generated updates by OpenAI Codex, 2026-11-15; existing Claude and team progress preserved. -->
# Progress

Deadline: **Sunday 15 November, 23:59** (local time of our Local Event). Aim to submit a first version early; the project can be edited and resubmitted until the deadline.

Status values: `todo`, `doing`, `done`, `blocked`.

## Tasks

| # | Task | Owner | Status | Notes |
|---|---|---|---|---|
| 1 | Agree on concept and scope (sites, date range, factors) | Qiming | done | Date-first tool; 2027–2030; sunlight, Earth contact, flatness, plus slip stability |
| 2 | Choose preset south-pole sites | Qiming | done | The 13 NASA Artemis III candidate regions |
| 3 | Ephemeris pipeline: Sun and Earth elevation over time for one site (flat horizon) | Claude (for Qiming) | done | `src/ephemeris.py`; checked against JPL Horizons at 10 points, within 0.002° elevation |
| 4 | Terrain horizon for preset sites, precomputed | Claude (for Qiming) | done | `data/terrain_horizons.txt` (13 sites), `data/horizon_calibration.json`. Before calibration: Earth visibility within 0.5 points of NASA at 9 of 13 sites; Sun differs 6.5 points on average, 17 at worst |
| 5 | Metrics per scenario (sunlit %, longest darkness, Earth visible %, longest blackout) | Claude (for Qiming) | done | `src/planner.py`, terrain skyline included; ran for 2027–2030 |
| 6 | Weighted score and ranking | Claude (for Qiming) | done | Done in `src/planner.py`: five limits, three-factor weighted score, slip stability columns, nearest passing dates, best dates per site, custom coordinates (no terrain), eclipse detection; 11 checks in `tests/test_planner.py` pass. Not done (dropped for time): Pareto set |
| 7 | App: scenario comparison view and timelines | Claude (for Qiming) | done | `src/app.py`: two-step flow, ranked map, site panel, sky panorama, visibility timeline, custom coordinates. Deployed: https://lunar-landing-navigator-team-of-aeers.streamlit.app/ |
| 8 | Site × date heatmap (robustness to delay) | Claude (for Qiming) | done | "Compare dates" tab in `src/app.py`; slip worst case shown per site |
| 9 | Demo: 7 slides or 30-second video, in English | Claude (for Qiming) | done | `docs/demo/` (PowerPoint and PDF), public at https://quentinliu-a11y.github.io/Lunar_Landing_Optimal_System/demo/Lunar_Landing_Navigator_TeamOfAEers.pdf |
| 10 | Project page text: summary, description, NASA data, references, AI use | Claude (for Qiming) | done | `docs/submission.md`; team to review and paste |
| 11 | Make all links public and test them in a private window | | todo | |
| 12 | Submit for judging | | todo | |

| 13 | Derive physical geometry and coordinate transformations | OpenAI Codex | done | `docs/physics-and-coordinates.md`: 24 projection round trips, cardinal directions, ENU bases, curvature and pixel-centre checks passed; no date-specific NASA-tool comparison. |
| 14 | Audit raw-raster pixel registration and recompute site coordinates if needed | Claude (for Qiming) | done | Confirmed: the first analysis used a half-pixel-shifted transform (+30 m in x, -30 m in y). Site coordinates were recomputed from the raw rasters with NASA's pixel-centre convention, x=(c-2528.5)*60, y=(2528.5-r)*60, and are stored in `data/terrain_horizons.txt`, which the code uses. `data/a3_region_visibility_stats.json` keeps the earlier coordinates (about 42 m off) and is marked as superseded for positions; its visibility values are unaffected. |

| 15 | Interactive polar atlas visual redesign | OpenAI Codex | done | Based on main f778f41; authentic NASA LROC mosaic, true-position clickable map, zoom/pan, hourly horizon explorer, lazy views and cached planner calls. 8 UI checks, 11 planner checks and Horizons checks passed; desktop and 390px browser layouts inspected. Merged and deployed 15 Nov. |

| 16 | Guided tour web page (four scenes from the team's storyboard) | Claude (for Qiming) | done | `docs/index.html` on GitHub Pages; ranking matches `planner.rank_for_date` in 162 checked cases; NASA imagery from GIBS and images.nasa.gov |
| 17 | 3D site scene | team member (JamieLEO), Claude | done | `docs/Lunar Landing Site Simulator (1).html`: now uses the team's 13 sites, hourly Sun/Earth directions and visibility from the planner (`src/export_sim_data.py`, `docs/data/sky/`), and each site's LOLA skyline; readouts match `planner.timeline` hour by hour in tested cases; ground surface and lander illustrative |
| 19 | Tour heading f(date, site, others) with step highlight and unfolding factors | Claude (for Qiming) | done | Team storyboard idea |
| 20 | Real star field (HYG catalogue) in the tour and the 3D view | Claude (for Qiming) | done | 3D star positions checked against `src/ephemeris.py` (0.0001°) |
| 21 | Realistic 3D: airless lighting and shadows, regolith texture, NASA Blue Marble Earth turned for the hour, Face Sun / Face Earth views, Play and Re-plan buttons, smooth sunrise/sunset | Claude (for Qiming) | done | Earth orientation checked against the almanac subsolar point (0.2°) |
| 18 | Lander presets with sources | team (helper research) | done | Nova-C 10° (IM-1, Wikipedia), crewed lander tilt 8° (NASA OIG IG-26-004); Blue Ghost slope not published |

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
- Interface basemap: NASA/GSFC/Arizona State University LROC WAC south-pole mosaic, served by NASA Moon Trek: https://trek.nasa.gov/moon/trekarcgis/rest/services/LRO_WAC_Mosaic_SPole60_100m_v02/ImageServer . Retrieved once as `data/lroc-south-pole.jpg` (245,467 bytes, 1200 x 1200 pixels); exact export URL and projection in `data/lroc-south-pole.source.json`. Display bounds +/-210 km in south polar stereographic coordinates; radius 1,737,400 m, central meridian 0, standard parallel -90. Export is 350 m/display pixel from a native 100 m/pixel service. Archival shadows are not selected-date illumination. Projection metadata checked; no independent landmark-registration audit performed.
- NASA PDS LOLA solar visibility metadata: https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/extras/illumination/img/avgvisib_85s_060m_201608.lbl ; polar projection catalog: https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/catalog/dsmap_polar.cat . Inspected for task 13; raw imagery not downloaded in that task. Earth label fetch unsuccessful; its disc definition remains unverified in this audit.
- NASA PDS LOLA scaling FAQ: https://pds-geosciences.wustl.edu/missions/lro/lola_faq.htm ; JPL Horizons manual: https://ssd.jpl.nasa.gov/horizons/manual.html ; NASA NAIF lunar frame tutorial: https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/Tutorials/pdf/individual_docs/23_lunar-earth_pck-fk.pdf . Consulted for physical and frame conventions; no Horizons ephemeris request executed.
- NASA Cross-Program Design Specification for Natural Environments, revision H, section 3.4.9: https://ntrs.nasa.gov/api/citations/20205007447/downloads/SLS-SPEC-159%20Cross-Program%20Design%20Specification%20for%20Natural%20Environments%20%28DSNE%29%20REVISION%20H.pdf . Physical background on lunar solar day and obliquity, not an adopted project requirement.
- LOLA elevation models LDEM_85S_40M and LDEM_75S_120M (PDS Geosciences Node, https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/): terrain skylines in `data/terrain_horizons.txt`.
- JPL Horizons API (https://ssd.jpl.nasa.gov/api/horizons.api), DE441: reference Sun and Earth azimuth/elevation for two south-pole sites, used to validate `src/ephemeris.py` (`tests/test_ephemeris.py`).
- LOLA average Sun and Earth visibility maps, 60 m/px, south pole (`avgvisib_85s_060m_201608.img`, `..._earth.img`), PDS Geosciences Node: https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/extras/illumination/img/ . Method: Mazarico et al. (2011), Icarus 211, 1066.
- Moon Trek `A3_Named_regions` service (Artemis III region outlines): https://trek.nasa.gov/moon/trekarcgis2/rest/services/A3_Named_regions/MapServer/0

### Partner agency data and other references (data, tools, libraries, images)
- Visual workflow: https://github.com/houxin0010/distinctive-ai-design and https://github.com/emilkowalski/skills (`emil-design-eng`, `animation-performance`). Existing Streamlit/Plotly stack; no new application dependencies. Playwright with local Edge and Streamlit AppTest used for validation. Real orbital imagery only; no generated media or NASA branding.
- Task 13: existing Python interpreter and standard-library `math`, `ast`, and `pathlib` for analytical checks; OpenAI Codex web search for primary-source documentation. No new runtime dependencies. USGS projection reference and NASA Earth-label retrieval were attempted but unavailable; neither supports a new verified result.
- Python libraries: Streamlit, Plotly, pandas, NumPy, PyERFA (see `requirements.txt`). PyERFA supplies the Earth and Moon position routines `epv00` and `moon98`.
- Moon rotation model: IAU Working Group on Cartographic Coordinates and Rotational Elements, 2009 report (Archinal et al., 2011, Celestial Mechanics and Dynamical Astronomy 109, 101).

### Web front end resources (15 Nov)
- NASA GIBS WMS (gibs.earthdata.nasa.gov), layers VIIRS_Black_Marble and BlueMarble_NextGeneration: Earth background, loaded by the visitor's browser.
- NASA image "Full Moon Rising Over Full Artemis II Stack at Launch Pad 39B", 1 Feb 2026, images.nasa.gov (Artemis II at the pad Full Snow Moon 02012026_3).
- NASA Scientific Visualization Studio "Full Moon" render from LRO LOLA data, images.nasa.gov (GSFC_20171208_Archive_e001861).
- Fonts: Cormorant Garamond, IBM Plex Sans, IBM Plex Mono (Google Fonts, SIL Open Font License).
- Lander slope figures: Wikipedia "IM-1" (Nova-C designed to stay upright on slopes of 10° or more, quoting Intuitive Machines' CTO); NASA OIG report IG-26-004 (tilt tolerance not to exceed 8° for NASA's human landing systems; Starship height 171 ft).
- `assets/icons/*.svg`: Lucide icons (ISC license), added by a team member; not used by the pages yet.
- NASA GIBS layer BlueMarble_NextGeneration also textures the Earth globe in the 3D scene; the globe is turned for the UTC time with the IERS Earth rotation angle (checked: subsolar point within 0.2° of the almanac formula).
- Star catalogue: HYG database (David Nash; Hipparcos, Yale Bright Star and Gliese catalogues; CC BY-SA 2.5) as packaged in d3-celestial `data/stars.6.json` (Olaf Frohn, BSD-3-Clause), converted to `docs/data/stars.json` (5,044 stars to magnitude 6). Used in the 3D sky (oriented with the IAU lunar rotation model; checked against `src/ephemeris.py`) and in the tour's star field.
- `docs/Lunar Landing Site Simulator (1).html`: teammate's 3D scene (three.js, MIT license, embedded in the file). On 15 Nov Claude replaced its mock sites, Sun/Earth model and horizon with the team's data, switched to airless lighting, and restyled it.

### AI tools used and for what
- Claude (Anthropic), 15 Nov evening: tour heading animation, real star field, 3D realism and camera views, the 7-slide demo deck (`docs/demo/`, built with pptxgenjs from screenshots of our own tool; slide backgrounds rendered from real HYG star positions; no AI-generated images), and this documentation update.
- Claude (Anthropic), 15 Nov: cinematic web front end `docs/index.html` (four scenes from the team's storyboard) and `src/export_web_data.py`, which exports the planner's results to `docs/data/sites.json`; checked that the page ranks exactly as `planner.rank_for_date` in 45 date/mission/slope cases. Star field and gradients are drawn in code; no AI-generated pictures.
- Claude (Anthropic): visual redesign of the interface on 15 Nov (dark theme, Sun amber / Earth blue throughout, site read-out bars marking the worst case if the landing slips). Layout, flow and all numbers unchanged; fonts Space Grotesk and IBM Plex Mono (Google Fonts, SIL Open Font License).
- Claude (Anthropic): reviewed and merged the OpenAI Codex interface (PR #1): confirmed the logic files were untouched, compared the basemap with a fresh NASA Moon Trek export (identical; flipped and 10 km shifted copies differ), ran it in headless Chrome, and adjusted label legibility, heat-map axes, map scrolling and the placement of the landing-slip result. Made the map test work with newer Plotly versions.
- OpenAI Codex: redesigned `src/app.py` as an ivory/forest polar atlas; added map selection, zoom/pan, an hourly horizon explorer, cached planner queries and on-demand workspace views. Preserved Claude's slope/weight/slip/date/custom-coordinate results. Added the visual theme, UI regression tests and image provenance. Reviewed actual desktop/mobile screenshots; offset crowded map labels without moving site coordinates and corrected axis spacing. Three logic modules are byte-for-byte unchanged from main f778f41. Tested 8 UI regressions, 11 planner checks, JPL Horizons comparisons, real map click/zoom/reset and timeline keyboard interaction. One local timeline update measured 384 ms; no real-device frame-rate claim. Independent code review was interrupted by a reviewer usage limit; the observed cross-view state issue was fixed and regression-tested.
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
