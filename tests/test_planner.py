"""Sanity checks for the date-specific planner.

AI-assisted: written by Claude (Anthropic), 2026-11-14.

Run:  python tests/test_planner.py
"""

import datetime as dt
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import planner  # noqa: E402

LOOKUP = planner.build_lookup(dt.date(2028, 1, 1), dt.date(2029, 1, 31))
LANDING = dt.datetime(2028, 1, 1)


def test_sites_and_skylines():
    assert len(LOOKUP.sites) == 13
    assert LOOKUP.sites["site"].is_unique
    assert all(len(s) == 360 for s in LOOKUP.sites["skyline"])
    assert LOOKUP.sites["lat"].between(-90, -83).all()


def test_ranking_rules():
    r = planner.rank_for_date(LOOKUP, LANDING, 14)
    for col in ("sun_window", "earth_window", "flatness", "score", "sun_window_worst", "earth_window_worst"):
        assert r[col].between(0, 1).all(), col
    assert list(r["rank"]) == list(range(1, 14))
    # every passing site is ranked above every failing site
    assert not r["passes"].iloc[r["passes"].sum():].any()
    assert ((r["fail_reasons"] == "") == r["passes"]).all()
    # the worst case over a slip window can never beat the chosen date
    assert (r["sun_window_worst"] <= r["sun_window"] + 1e-12).all()
    assert (r["earth_window_worst"] <= r["earth_window"] + 1e-12).all()
    # score = dynamic weights x margins; a dynamic weight is its base share x stability
    assert np.allclose(r["score"], r["w_sun"] * r["sun_score"] + r["w_earth"] * r["earth_score"] + r["w_flat"] * r["flatness"])
    assert np.allclose(r["w_sun"] * 3 * r["sun_window"], r["sun_window_worst"]) and np.allclose(r["w_flat"], 1 / 3)
    assert np.allclose(r.loc[r["passes"], "sun_score"], (r.loc[r["passes"], "sun_window"] - 0.95) / 0.05)


def test_limits_and_weights():
    loose = planner.rank_for_date(LOOKUP, LANDING, 14, 0, 0, 0, 0, 90)
    assert loose["passes"].all()
    steep = planner.rank_for_date(LOOKUP, LANDING, 14, 0, 0, 0, 0, max_slope_deg=3.0)
    assert (steep.loc[~steep["passes"], "slope_mean_deg"] > 3.0).all()
    sun_only = planner.rank_for_date(LOOKUP, LANDING, 14, 0, 0, 0, 0, 90, weights={"earth": 0, "flatness": 0})
    # With no limits the margin is the ratio itself, so the score is ratio x stability = the worst-case ratio.
    assert np.allclose(sun_only["score"], sun_only["sun_window_worst"])
    try:
        planner.rank_for_date(LOOKUP, LANDING, 14, weights={"sunlight": -1})
        raise AssertionError("negative weight accepted")
    except ValueError:
        pass


def test_window_matches_timeline():
    r = planner.rank_for_date(LOOKUP, LANDING, 14).set_index("site")
    tl = planner.timeline(LOOKUP, "Malapert Massif", LANDING, 14)
    assert len(tl) == 14 * 24 + 1                      # chart includes the end point
    assert abs(tl["sun_up"].iloc[:-1].mean() - r.loc["Malapert Massif", "sun_window"]) < 1e-12
    assert ((tl["sun_margin"] > 0) == tl["sun_up"]).all()


def test_date_range_is_enforced():
    for bad in (dt.datetime(2027, 12, 31), dt.datetime(2029, 2, 1)):
        try:
            planner.rank_for_date(LOOKUP, bad, 14)
            raise AssertionError("out-of-range date accepted")
        except ValueError:
            pass


def test_late_time_on_last_day_is_accepted():
    late = dt.datetime.combine(LOOKUP.end, dt.time(23, 59))
    r = planner.rank_for_date(LOOKUP, late, 60)
    assert len(r) == 13
    tl = planner.timeline(LOOKUP, "Haworth", late, 60)
    assert str(tl["time_utc"].iloc[0])[:13] == f"{LOOKUP.end} 23"


def test_eclipse_only_counted_while_sun_visible():
    assert not ((LOOKUP.eclipse > 0) & ~LOOKUP.sun_up).any()


def test_date_scan_matches_ranking():
    scan = planner.date_scan(LOOKUP, 14, hour_utc=7).set_index(["date", "site"])
    for day in (dt.date(2028, 1, 1), dt.date(2028, 9, 17)):
        r = planner.rank_for_date(LOOKUP, dt.datetime.combine(day, dt.time(7)), 14).set_index("site")
        for site in r.index:
            assert abs(scan.loc[(day, site), "sun_window"] - r.loc[site, "sun_window"]) < 1e-12
            assert abs(scan.loc[(day, site), "earth_window"] - r.loc[site, "earth_window"]) < 1e-12


def test_calendar_agrees_with_ranking():
    cal = planner.passing_calendar(LOOKUP, 14)
    day = cal[cal["date"] == LANDING.date()].set_index("site")
    r = planner.rank_for_date(LOOKUP, LANDING, 14).set_index("site")
    assert (day["passes"] == r.loc[day.index, "passes"]).all()
    near = planner.nearest_passing_dates(LOOKUP, LANDING, 14).set_index("site")
    assert (near["passes_on_date"] == r.loc[near.index, "passes"]).all()


def test_known_lunar_eclipses_are_detected():
    # Lunar eclipses in this period, from published eclipse lists (recalled, not re-fetched):
    # 2028-01-12, 2028-07-06, 2028-12-31.
    days = {str(t)[:10] for t in LOOKUP.times[(LOOKUP.eclipse > 0).any(axis=0)]}
    assert {"2028-01-12", "2028-07-06", "2028-12-31"} <= days, days
    # (counted only where the Sun was above the skyline at that site; at least one site sees each)


def test_custom_site_at_the_pole_and_equator():
    polar, tl = planner.custom_site(-89.9, 0.0, LANDING, 14)
    assert polar["terrain_included"] is True and len(tl) == 14 * 24 + 1      # inside the LOLA terrain grid
    flat, _ = planner.custom_site(-89.9, 0.0, LANDING, 14, use_terrain=False)
    assert flat["terrain_included"] is False and flat["sun_window"] >= polar["sun_window"]
    assert abs(polar["max_sun_el_window"]) < 2.0       # Sun hugs the horizon near the pole
    equator, _ = planner.custom_site(0.67, 23.47, dt.datetime(2028, 1, 5), 14)
    assert equator["terrain_included"] is False                 # outside the grid: flat horizon
    assert equator["max_sun_el_window"] > 80           # Sun passes nearly overhead
    assert equator["earth_window"] == 1.0              # near side: Earth always up


def test_terrain_grid_matches_named_sites():
    """The 500 m LOLA grid reproduces the 13 sites' heights and, roughly, their 40/120 m skylines."""
    import terrain
    from sites import load_sites
    for r in load_sites().itertuples():
        sky, h = terrain.skyline(r.lat, r.lon)
        assert abs(h - r.height_m) < 60, r.site
        assert np.sqrt(((sky - r.skyline) ** 2).mean()) < 2.5, r.site


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"OK: {len(tests)} planner checks passed")
