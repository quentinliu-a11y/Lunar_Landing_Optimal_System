# Design principles

Status of each item: **Decided** (agreed by the team lead), **Proposed** (suggested, awaiting agreement), **Measured** (taken from NASA data).

AI-assisted document: drafted by Claude (Anthropic) from team decisions and the data analysis in section 3.

## 1. What the tool is

- A planning tool used on Earth, in a web browser, by people choosing where and when to land. It is not flight software and does not run on the lander. **Decided**
- Date first: the user picks a landing date, sees the conditions for that date, and is taken to a map of recommended landing sites. **Decided**
- Recommendations come from ranking a fixed list of named candidate sites, not from scoring every map pixel. **Decided**
- Responses to a date change should appear within a second or two. Heavy calculations are done in advance and saved. **Decided** (lookup table built at start-up; the web pages read precomputed exports)

## 2. Factors

| Factor | Changes with date? | Status |
|---|---|---|
| Sunlight ratio | Yes | Decided (top 3) |
| Earth communication availability | Yes | Decided (top 3) |
| Flatness (slope) | No | Decided (top 3) |
| Longest continuous darkness | Yes | Shown, not a limit or score factor |
| Longest communication blackout | Yes | Shown, not a limit or score factor |
| Surface roughness, distance to permanently shadowed regions, surface temperature, mean solar elevation | Mixed | Proposed |

## 3. What the real data says (Measured)

Source: NASA LOLA average-visibility maps, 60 m/pixel, south of 85°S, simulated at 1-hour steps over about 18.6 years, at surface level. Numbers and method are in `data/a3_region_visibility_stats.json`.

Whole map (72,300 km²):

| Question | Answer |
|---|---|
| Highest long-term sunlight anywhere | **88.4%**, on the Connecting Ridge (89.475°S, 137.6°W) |
| Pixels with sunlight ≥ 90% | **None** |
| Pixels with sunlight ≥ 80% | 19 pixels (about 0.07 km²) |
| Pixels with sunlight ≥ 70% | 231 pixels (about 0.8 km²) |
| Area with Earth visibility ≥ 95% | 0.83% of the map; some pixels reach 100% |
| Pixels with both ≥ 80% | **None** |
| Pixels with both ≥ 70% | 4 pixels |
| Pixels with both ≥ 50% | 17,452 pixels (about 63 km²) |
| Best spot for both together | Malapert Massif (85.954°S, 3.4°W): sunlight 75.8%, Earth 71.7% |

Best pixel in each Artemis III region:

| Region | Best sunlight | Best Earth visibility | Best spot for both (sunlight / Earth) |
|---|---|---|---|
| Connecting Ridge | 88.4% | 58.7% | 71.9% / 58.7% |
| Peak Near Shackleton | 86.0% | 60.6% | 64.7% / 60.6% |
| Nobile Rim 1 | 83.1% | 100% | 67.5% / 73.7% |
| de Gerlache Rim | 82.7% | 61.8% | 69.4% / 61.8% |
| Malapert Massif | 81.9% | 100% | 75.8% / 71.7% |
| Connecting Ridge Extension | 79.4% | 59.4% | 60.4% / 59.4% |
| de Gerlache-Kocher Massif | 78.5% | 60.6% | 63.0% / 60.6% |
| de Gerlache Rim 2 | 75.1% | 61.8% | 69.4% / 61.8% |
| Leibnitz Beta Plateau | 74.7% | 100% | 67.6% / 80.6% |
| Haworth | 70.5% | 82.2% | 67.2% / 69.6% |
| Faustini Rim A | 65.9% | 52.4% | 51.8% / 51.5% |

Amundsen Rim (57.1% / 62.8%) and Nobile Rim 2 (52.7% / 62.8%) were added later; they sit in the corners of the map beyond 85°S. de Gerlache Rim and de Gerlache Rim 2 overlap, so the tool uses the best spot of Rim 2 outside Rim (61.2% / 59.6%).

What this means:

- A 95% long-term limit on sunlight is impossible: no location reaches 90%.
- The best-lit places and the best-connected places are mostly different. Sites near the pole have the most sunlight but see Earth only about 60% of the time; Earth-facing heights see Earth always but have less sunlight.
- Good spots are tiny, tens to hundreds of metres across, so the exact landing point inside a region matters more than the region.
- These are long-term averages. They do not say what happens in the two weeks after a particular landing date.

## 4. Hard limits

Sites that fail a limit are shown greyed out with the reason, and are not ranked. Every limit is a user setting with a default. **Decided in principle; default numbers Proposed**

Two kinds of limit, because the data in section 3 rules out a single 95% rule:

| Limit | Measured over | Default | Basis |
|---|---|---|---|
| Long-term sunlight | 18.6-year average | ≥ 50% | Measured: 63 km² meets this together with the Earth limit below |
| Long-term Earth visibility | 18.6-year average | ≥ 50% | Same |
| Mission-window sunlight | Mission window after the chosen landing date | ≥ 95% | Team target. Checked: with a 14-day window, 955 of 18,993 site-and-date combinations in 2027–2030 (5.0%) meet this together with the Earth limit |
| Mission-window Earth visibility | Same window | ≥ 95% | Same check |
| Slope | Fixed; mean slope within 120 m of the site | ≤ 10° | Default, adjustable. Tour presets: Nova-C class 10° (IM-1), crewed lander 8° (NASA OIG IG-26-004 tilt limit), or custom. Measured mean slopes range from 2.8° (Haworth) to 7.9° (Connecting Ridge); Connecting Ridge reaches 16.5° at its steepest point within 120 m |

- Default mission window: 14 days; user-set 1–60 days. **Decided**
- When no site passes on a date, the tool says so and points to the nearest date on which one does. **Decided, implemented**
- Date-specific check (terrain included, calibrated to the NASA long-term values): every one of the 13 sites reaches 95%/95% on some dates, from 14 dates (Faustini Rim A) to 155 (Nobile Rim 1) out of 1,461. Lowering both limits to 90% gives 1,436 combinations, 80% gives 2,644.

## 5. Scoring

Applied to sites that pass the limits. **Proposed**

- Each factor is scaled to 0–1, multiplied by its weight and summed.
- Implemented so far (`planner.rank_for_date`): three factors, sunlight (mission-window ratio), Earth (mission-window ratio) and flatness (1 − mean slope ÷ slope limit), with equal weights by default and user-set weights accepted. The weight ingredients and the stability adjustment below are not implemented yet.
- A factor's weight combines: mission importance (set by mission type), separating power (whether the factor differs between sites), and data confidence (how trustworthy our number is).
- Stability over time adjusts each site's values, not the factor weights: for factors that change with date, the value used is pulled toward its worst case within a slip window around the chosen date (default ±14 days). A site that stays good when the date slips scores higher than one that is good only on the chosen day.
- Weights are always shown, and the user can override them.
- Exact formulas are not written yet.

## 6. Interface

**Implemented** in the analysis app; the guided tour and 3D view (see README) add a plain-language path for non-specialists.

- True top-down polar map from real LOLA terrain, with sites as ranked, colour-coded markers.
- Horizon panorama for the selected site: the 360° terrain skyline with the Sun's and Earth's paths drawn over it. Earth and Sun must appear near the horizon, as they really do at the pole.
- Date slider that updates map, ranking and panorama together.
- Scorecard per site showing each factor, its weight, and any limit it fails.

## 7. Technology

**Decided**: Python engine; Streamlit + Plotly analysis app on Streamlit Community Cloud; static HTML/JavaScript guided tour and three.js 3D view on GitHub Pages; demo as a 7-slide deck (`docs/demo/`).
