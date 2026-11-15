<!-- AI-assisted: drafted by Claude (Anthropic), 2026-11-15, for the team to review before pasting into the project page. -->
# Project page text

Paste each part into the matching field of the Space Apps project page. Items in [brackets] must be filled in by the team.

## Project name

Lunar Landing Navigator

## High-level summary (short)

At the lunar south pole the Sun and Earth stay within a few degrees of the horizon, so whether a lander has power and a radio link depends on the exact landing date, not only on the place. Lunar Landing Navigator is a planning tool that starts from the date: choose a landing date, time and mission length, and it ranks the 13 Artemis III candidate regions on sunlight, Earth contact and flatness for that mission, using NASA LRO terrain data. It also shows how each result changes if the landing slips, so planners can choose a site that survives a schedule change.

## Link to demo

https://quentinliu-a11y.github.io/Lunar_Landing_Optimal_System/demo/Lunar_Landing_Navigator_TeamOfAEers.pdf

## Link to project

https://github.com/quentinliu-a11y/Lunar_Landing_Optimal_System
Guided tour (start here): https://quentinliu-a11y.github.io/Lunar_Landing_Optimal_System/
Full analysis app: https://lunar-landing-navigator-team-of-aeers.streamlit.app/

## Detailed description

**What it does.** The tool has two steps. In step 1 the user picks a planned landing date and time (2027–2030, UTC) and the length of the surface mission (1–60 days). In step 2 a map of the south pole shows the 13 Artemis III candidate regions, coloured by whether they meet the mission limits and numbered by rank. Selecting a site shows the share of the mission with the Sun above the terrain, the share with Earth above the terrain, the slope, the time until the Sun and Earth next set, any lunar eclipse during the mission, and the worst case if the landing slips by a chosen number of days. A panorama draws the terrain skyline around the site with the hourly path of the Sun and Earth. A second view compares every landing date of a year for all sites, and a third evaluates any coordinates: near the south pole (within about 300 km) it computes the terrain skyline for that point from a NASA LOLA elevation grid and shows it with the Sun and Earth paths. A site table lists 18 measures for all 13 sites and downloads as CSV.

**The Earth side of the link.** For each site and mission the tool also shows which of NASA's three Deep Space Network complexes (Goldstone, Madrid, Canberra) can see the Moon above 10°, hour by hour, and how often rain at those antennas may weaken a high-rate Ka-band link, using monthly precipitation climatology (not a forecast). The Moon has no weather; on Earth, rain matters for Ka band and hardly at all for X band. This is shown alongside the ranking and does not change it.

**Why Earth's rotation does not change the results.** Where Earth appears in the lunar sky depends on the Moon's orbit and orientation, both modelled hourly; Earth's spin only changes which side of Earth faces the Moon. That matters for which ground antenna is in view, which is why the Deep Space Network view above models Earth's rotation (IAU 2006/2000A).

**How it works.** For each site we computed the terrain skyline in 360 directions from NASA LOLA elevation models (40 m per pixel within 25 km, 120 m per pixel out to 300 km), for a mast 2 m above the surface. Sun and Earth directions are computed for every hour of 2027–2030 with the ERFA library and the IAU lunar rotation model. A body counts as visible when the top edge of its disc is above the skyline. Results are stored in a lookup table with running totals, so any mission window is answered immediately. Sites must pass hard limits (by default at least 95% sunlight and 95% Earth contact during the mission, at least 50% of each in the long term, and a mean slope of at most 10°); sites that pass are ordered by a weighted score of sunlight, Earth contact and flatness. The user can change every limit and weight.

**Why it matters.** Long-term average maps hide large date-to-date changes. Example from the tool: Nobile Rim 1 has 100% sunlight and 100% Earth contact for a 14-day mission landing on 1 January 2028, but if that landing slips by up to 14 days the worst case is 41% sunlight and 46% Earth contact. On that date only 2 of the 13 sites meet the default limits.

**How we checked it.** Sun and Earth positions agree with NASA JPL Horizons (DE441) within 0.002° in elevation and 0.008° in azimuth at 10 reference points. The map image is identical to the NASA Moon Trek export for the stated area. Deep Space Network Moon elevations agree with the astropy library within 0.001°. The terrain grid used for custom coordinates reproduces the 13 sites' heights within 40 m and their high-resolution skylines with a mean RMS difference of 0.83°. The ranking rules and the interface are covered by automated tests in the repository (21 checks).

**Limits we want judges to know.** Results are estimates. Our uncalibrated terrain result differed from NASA's long-term Sun visibility by 6.5 percentage points on average, so each site's skyline is adjusted by one constant so that its 18.6-year average equals NASA's published value. Eclipse hours are reported but not subtracted from the sunlight share. "Earth visible" means any part of Earth's disc is above the terrain; it does not guarantee a link to a particular ground station. Custom coordinates use a coarser (500 m), uncalibrated terrain grid: for the 13 named sites it differs from our calibrated results by about 10 percentage points on average, more when the Sun or Earth grazes a ridge; outside about 80°S they fall back to a flat horizon. The 10° slope limit is a default chosen by the team, not a NASA requirement.

**3D site view.** From the tour, the chosen site opens in 3D for the chosen date and mission. The Sun and Earth move along their computed hourly paths, the ridge around the lander follows the site's NASA LOLA skyline, real stars (HYG catalogue) and a NASA Blue Marble Earth are placed for the exact hour, and sunlight casts long shadows with no atmosphere to soften them. Users can play the mission, follow the Sun or Earth from the lander, and watch the Sun drop behind the terrain when the data says it does. The ground near the lander and the lander model are illustrative and labelled as such.

**Two ways in.** A guided tour for non-specialists (a web page that flies from Earth to the lunar south pole, with plain-language verdicts) and a full analysis app with every chart and setting. Both use the same results; the tour's ranking was checked to match the analysis app in 162 date, mission-length and slope cases.

**Tools.** Python, Streamlit, Plotly, NumPy, pandas, pyerfa; HTML, CSS and JavaScript for the tour.

## NASA data

- LRO LOLA elevation models LDEM_85S_40M and LDEM_75S_120M (PDS Geosciences Node): terrain skyline and slope.
- LRO LOLA long-term average Sun and Earth visibility maps (PDS Geosciences Node): calibration and long-term limits.
- LRO LOLA south-pole elevation service LRO_LOLA_DEM_SPole45_100mp_v04 (NASA Moon Trek), resampled to 500 m: terrain for custom coordinates.
- NASA Deep Space Network complex locations (Goldstone, Madrid, Canberra).
- Artemis III candidate landing regions (NASA Moon Trek): the list and positions of sites.
- LROC WAC south-pole mosaic (NASA/GSFC/Arizona State University, via NASA Moon Trek): map background.
- NASA JPL Horizons: independent check of Sun and Earth positions.
- NASA GIBS (Global Imagery Browse Services): VIIRS Black Marble night lights and Blue Marble Next Generation, shown with the day/night line computed for the current time.
- NASA images: full Moon over Artemis II at Launch Pad 39B (1 Feb 2026); NASA Scientific Visualization Studio full-Moon render from LRO LOLA data.
- NASA Moon Trek and LROC QuickMap were used to explore the data.
- Star positions: HYG database (Hipparcos, Yale Bright Star and Gliese catalogues), via the open-source d3-celestial project.

## References

- ERFA (Essential Routines for Fundamental Astronomy), through the pyerfa package.
- IAU Working Group on Cartographic Coordinates and Rotational Elements, 2009 report: lunar rotation model.
- Streamlit, Plotly, NumPy, pandas (open-source libraries); astropy for an independent check.
- Precipitation climatology near the DSN complexes: NOAA 1991–2020 normals (Barstow, California), AEMET normals (Madrid Cuatro Vientos), Australian Bureau of Meteorology averages (Canberra Airport).
- Fonts: Space Grotesk and IBM Plex Mono (SIL Open Font License).
- Full list with links: `PROGRESS.md` in the repository.

## Use of artificial intelligence

We used AI tools and disclose them here and in the repository (`PROGRESS.md`, "AI tools used and for what"; AI-written files carry a comment saying so).

- Claude (Anthropic): wrote and tested the calculation code, reviewed the interface, redesigned its visual style, built the guided-tour web page from the team's storyboard, drafted the documentation, this text and the demo slides.
- OpenAI Codex: built the first version of the interface and wrote the derivations in `docs/physics-and-coordinates.md`.
- The illustrative 3D scene (scene IV of the tour) was built by a team member with AI assistance; it is labelled in the page as an illustrative model.
- The concept, the choice of factors and limits, and all decisions were made by the team, who directed and reviewed the AI work.
- No AI-generated images, video or audio are used. NASA imagery is shown unaltered and no NASA logos are used.
