# Lunar Landing Optimal System

Team project for the **2026 NASA Space Apps Challenge** (14–15 November 2026), challenge: [Lunar Landing Site Navigator](https://www.spaceappschallenge.org/2026/challenges/lunar-landing-site-navigator/).

**Submission deadline: Sunday 15 November, 23:59 (local time of our Local Event).**

## The problem

Missions to the Moon's south pole depend on two things at the landing site:

- **Sun above the horizon** → solar power and thermal conditions
- **Earth above the horizon** → direct communication without a relay satellite

Near the pole both change a lot with a small shift in location or landing date, and launch dates slip. The data exists (Quickmap, Moon Trek, JPL Horizons), but comparing several site-and-date scenarios quickly is hard.

## Our concept (draft, to be agreed by the team)

A trade-off explorer for landing sites and dates, in three layers:

1. **Visibility engine.** Input: site coordinates and a date range. Output: Sun and Earth elevation over time compared with the terrain horizon, giving "sunlit" and "Earth visible" timelines.
2. **Multi-factor score.** Turns the timelines into metrics per scenario, combines them with user-set weights, and shows a ranking together with the Pareto set (scenarios no other scenario beats on every factor).
3. **Robustness to delay.** A site × landing-date heatmap of the score, to find sites that stay good when the launch slips.

Candidate factors: percent of time sunlit, longest continuous darkness, mean solar elevation, percent of time Earth is visible, longest communication blackout, local slope.

## Repository layout

| Path | Contents |
|---|---|
| `docs/space-apps-2026-reference.md` | Challenge statement, resources, judging criteria, submission rules |
| `docs/design-principles.md` | Design decisions, hard limits and the measured visibility figures |
| `docs/ui-interface.md` | Contract between the logic code and the visual interface |
| `AGENTS.md` | Instructions for AI agents working in this repo: decisions, open questions, rules |
| `PROGRESS.md` | Task board: who is doing what, and status |
| `src/` | Code |
| `data/` | Small processed data files (keep large raw files out of git) |

## Run it

Needs Python 3.10 or newer.

```
pip install -r requirements.txt
streamlit run src/app.py
```

The app opens in your browser. `src/app.py` is a reference interface; see `docs/ui-interface.md` for how a different interface should call the logic.

## How we work

- Update `PROGRESS.md` when you start or finish a task.
- Small, frequent commits; pull before you push.
- Record every dataset, tool, library, image and piece of AI-assisted work in `PROGRESS.md` under "References and AI use". The submission form requires all of them.

## Team

| Name | GitHub | Role |
|---|---|---|
| Qiming | @quentinliu-a11y | |
| | | |
