# Lunar Landing Optimal System

A planning tool that answers one question for lunar south-pole missions: **if we land on this date, which sites have sunlight and a link to Earth, and what happens if the date slips?**

Team entry for the 2026 NASA Space Apps Challenge, challenge [Lunar Landing Site Navigator](https://www.spaceappschallenge.org/2026/challenges/lunar-landing-site-navigator/).

> **Start here (guided tour): https://quentinliu-a11y.github.io/Lunar_Landing_Optimal_System/**
>
> **Full analysis app: https://lunar-landing-navigator-team-of-aeers.streamlit.app/**
>
> **Demo slides (PDF): https://quentinliu-a11y.github.io/Lunar_Landing_Optimal_System/demo/Lunar_Landing_Navigator_TeamOfAEers.pdf**
>
> Status, 15 November 2026: the calculation engine, the guided tour, the 3D site view and the analysis app are complete, tested and deployed. Text for the project page is in `docs/submission.md`.

## The problem

A lander at the Moon's south pole needs the Sun above the horizon for power and the Earth above the horizon to talk home without a relay satellite. Near the pole both sit within a few degrees of the horizon, so a ridge a few kilometres away can hide either one for days. Whether a site works depends on the exact place and the exact date, and launch dates slip.

NASA's own tools hold the data, but comparing several sites across several dates means working through them one case at a time.

## What the tool does

There are two ways in, built on the same results.

**Guided tour** (`docs/index.html`, for anyone): a four-scene web page. The heading reads *f*(date, site, others) and fills in as you go.
1. **Earth at night**, with today's day/night line computed for the current time.
2. **Plan the landing**: date, 1–60 days on the surface, and the lander's slope limit (Nova-C class 10°, crewed lander 8°, or your own).
3. **The south pole**: the 13 sites ranked for that plan, with plain-language verdicts for power, radio contact, ground slope and what happens if the date slips, and the nearest dates that work when a site fails. "Others" in the heading unfolds into these factors.
4. **Stand at the site in 3D**: the Sun and Earth move along their real hourly paths for that site, the ridge follows its NASA LOLA skyline, the sky shows real stars and a NASA Blue Marble Earth turned for the hour, and sunlight casts long airless shadows. Buttons play the mission, follow the Sun or Earth from the lander, or go back and re-plan.

**Analysis app** (`src/app.py`, Streamlit, for specialists): every number, chart and setting, including the sky panorama, visibility timelines, date heat maps, adjustable limits and weights, and custom coordinates.

For each of the 13 Artemis III candidate regions it reports:

| Result | Meaning |
|---|---|
| Sunlight ratio | Share of the mission with the Sun visible above the terrain |
| Earth contact ratio | Share of the mission with Earth visible above the terrain |
| Flatness | Mean slope within 120 m of the site |
| Longest darkness and longest blackout | The worst single gap in power and in contact |
| Time to sunset and Earthset | Counted from landing |
| Worst case if the date slips | Lowest sunlight and contact ratios if landing moves up to 14 days either way |
| Nearest workable date | The closest landing date on which the site passes every limit |
| Eclipse hours | Hours when Earth blocks the Sun |

Sites must pass limits the user can change (defaults: long-term sunlight and Earth visibility at least 50%, mission sunlight and contact at least 95%, slope at most 10°). Passing sites are ranked by a weighted score of sunlight, Earth contact and flatness, with the weights shown and adjustable. Any latitude and longitude can also be entered, as a rougher estimate without terrain.

Changing the date is instant: all Sun and Earth positions for 2027–2030 are computed once at start-up (about 1.5 seconds) and looked up afterwards.

## What we found

- **No place at the south pole is sunlit 95% of the time in the long run.** The best spot, on the Connecting Ridge, reaches 88.4%. Nowhere has both sunlight and Earth visibility above 80%.
- **Over a two-week mission the picture changes.** With the right landing date a site can have both for the whole mission. Across 2027–2030, 5% of site-and-date combinations reach 95% for both.
- **A perfect date can be fragile.** Landing on 1 January 2028, Nobile Rim 1 has 100% sunlight and 100% Earth contact for 14 days. Move the landing by up to two weeks and its sunlight can fall to 41%.
- **The best-lit site is the steepest.** The Connecting Ridge site averages 7.9° of slope and reaches 16.5° nearby.

## NASA data used

| Data | Used for |
|---|---|
| LOLA average Sun and Earth visibility maps, 60 m/pixel (LRO, PDS Geosciences Node) | Choosing the best point in each region; long-term limits; calibration |
| LOLA elevation models LDEM_85S_40M and LDEM_75S_120M (LRO, PDS Geosciences Node) | Terrain skyline around each site; slope |
| LROC WAC south-pole mosaic (LRO, NASA/GSFC/Arizona State University, via Moon Trek) | Background image of the map; display only |
| Artemis III candidate region outlines (Moon Trek) | The list of candidate sites |
| JPL Horizons (DE441) | Checking our Sun and Earth positions |
| GIBS layers VIIRS Black Marble and Blue Marble Next Generation (NASA Worldview) | Earth at night and by day in the tour; Earth globe in the 3D view |
| NASA images: full Moon over Artemis II at Pad 39B; SVS full-Moon render from LOLA data | Tour backgrounds |

Exact files, links and other references are listed in `PROGRESS.md`.

### Challenge and official data sources

- Challenge: [Lunar Landing Site Navigator](https://www.spaceappschallenge.org/2026/challenges/lunar-landing-site-navigator/) — 2026 NASA Space Apps Challenge
- [NASA JPL Horizons](https://ssd.jpl.nasa.gov/horizons/) — Sun and Earth ephemeris (DE441); API: https://ssd.jpl.nasa.gov/api/horizons.api
- [Quickmap](https://quickmap.lroc.asu.edu/) — LRO terrain and imagery
- [Moon Trek](https://trek.nasa.gov/moon/) — LRO terrain, imagery and Artemis III region outlines
- [LOLA illumination and elevation data, PDS Geosciences Node](https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/extras/illumination/img/) — visibility maps and elevation models

## How we know it is right

- **Sun and Earth positions** agree with JPL Horizons to within 0.002° in elevation and 0.008° in azimuth at 10 test points (`tests/test_ephemeris.py`).
- **Earth visibility**, averaged over 18.6 years with our terrain skylines, is within 0.5 percentage points of NASA's long-term map at 9 of the 13 sites; the largest difference is 12.9 points.
- **Sun visibility** differs from NASA's map by 6.5 points on average and 17 at worst. Near the pole the Sun grazes the skyline, so tens of metres of position or terrain change the answer. We therefore shift each site's skyline by one constant so that our long-term average equals NASA's figure, and use that calibrated skyline for specific dates.
- **Lunar eclipses** found by the tool in 2027–2030 fall on the dates of the known eclipses in that period.
- The ranking rules are covered by `tests/test_planner.py`.
- **The guided tour** reproduces the analysis app's ranking, pass/fail and slip worst case exactly in 162 checked combinations of date, mission length (1–60 days) and slope limit.
- **The 3D view** uses the planner's hourly Sun/Earth directions and visibility directly; its readouts match `planner.timeline` hour by hour in the tested cases. Its star positions match our lunar rotation model to 0.0001°, and the Earth globe's subsolar point agrees with the standard almanac formula within 0.2°.
- **The map image** is byte-for-byte the NASA Moon Trek export for the stated area, and is placed on the map at that same area; flipped or shifted copies do not match.

## Limits of the tool

- Results for a specific date are estimates anchored to NASA's long-term data, not mission-grade predictions.
- "Earth visible" means some part of Earth's disc is above the terrain. A particular ground station can still be out of view.
- Sunlight is counted as yes or no; received power is not computed, and eclipse hours are reported but not subtracted.
- Slope comes from a 40 m elevation model and says nothing about boulders or lander-leg-scale hazards.
- Custom coordinates have no terrain and no slope.
- In the 3D view the ground near the lander, the rocks, the lander model and the power figure are illustrative; the Sun, Earth, stars, skyline angles and visibility are computed.
- Each region is represented by a single point, its best 60 m pixel for combined sunlight and Earth visibility.

## Run it

Needs Python 3.10 or newer.

```
pip install -r requirements.txt
streamlit run src/app.py                 # analysis app
python -m http.server -d docs 8000       # guided tour and 3D view at http://localhost:8000
python tests/test_ephemeris.py
python tests/test_planner.py
python tests/test_interface.py
```

After changing `src/planner.py` or `data/`, regenerate the files the web pages read:

```
cd src && python export_web_data.py && python export_sim_data.py
```

## Repository layout

| Path | Contents |
|---|---|
| `src/ephemeris.py` | Sun and Earth direction at any point on the Moon |
| `src/sites.py` | Candidate sites with long-term visibility, skyline and slope |
| `src/planner.py` | Date-specific conditions, limits, ranking, stability, nearest dates, custom coordinates |
| `src/app.py` | Analysis app (Streamlit): date page, ranked map, sky panorama, date comparison, custom coordinates |
| `src/export_web_data.py` | Exports daily Sun/Earth visibility per site to `docs/data/sites.json` for the guided tour |
| `src/export_sim_data.py` | Exports hourly Sun/Earth directions, visibility and skylines to `docs/data/sky/` and `docs/data/sim_sites.json` for the 3D view |
| `docs/index.html` | Guided tour (GitHub Pages) |
| `docs/Lunar Landing Site Simulator (1).html` | 3D site view, opened from the tour |
| `docs/data/` | Data files read by the web pages, including `stars.json` (HYG star catalogue) |
| `docs/demo/` | Demo slides (PowerPoint and PDF) |
| `docs/submission.md` | Text for the Space Apps project page |
| `data/` | Processed NASA data: skylines, calibration, slopes, visibility statistics |
| `tests/` | Checks against JPL Horizons, of the ranking rules, and of the interface |
| `docs/design-principles.md` | Design decisions, limits and measured figures |
| `docs/physics-and-coordinates.md` | Derivation of the geometry and how it maps to the code |
| `docs/ui-interface.md` | Contract between the calculation engine and the interface |
| `docs/space-apps-2026-reference.md` | Challenge statement, judging criteria and submission rules |
| `AGENTS.md` | Instructions for AI agents working in this repository |
| `PROGRESS.md` | Task board, decisions, references and AI-use log |

## Use of AI

AI tools were used to write code and documents and to process the NASA data, under the team's direction. The concept, the date-first flow, the choice of factors and the limits are the team's. Every AI-assisted file says so at the top, and `PROGRESS.md` lists which tool did what.

## Team

Team_of_AEers

| Name | GitHub | Role |
|---|---|---|
| Qiming | @quentinliu-a11y | |
| Surani | @amansurani92 | Solar power & comms |
| Ratnesh | | |
| Zhehao | | |
