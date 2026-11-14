"""Lunar Landing Optimal System - working interface.

AI-assisted: written by Claude (Anthropic), 2026-11-14.

Flow: step 1 pick a planned landing date, step 2 see the candidate sites
ranked for that date, open one, compare dates, or try custom coordinates.

All numbers come from src/planner.py; nothing is calculated here.

Run with:  streamlit run src/app.py
"""

from __future__ import annotations

import datetime as dt
import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import planner
from sites import MOON_RADIUS_M

st.set_page_config(page_title="Lunar Landing Optimal System", layout="wide")

FIRST_DAY, LAST_DAY = dt.date(2027, 1, 1), dt.date(2030, 12, 31)
PASS, FAIL, PICK = "#2a9d8f", "#8d99ae", "#e76f51"
SUN, EARTH, GROUND = "#f4a261", "#4ea8de", "#3d4a5c"
BG = "#0f1722"
ESTIMATE_NOTE = (
    "Date results are estimates: real terrain skylines from NASA LOLA elevation data, "
    "calibrated so the long-term average matches NASA's visibility maps."
)


@st.cache_resource(show_spinner="Computing Sun and Earth positions for 2027-2030...")
def get_lookup() -> planner.Lookup:
    return planner.build_lookup(FIRST_DAY, LAST_DAY)


def init_state() -> None:
    st.session_state.setdefault("step", 1)
    st.session_state.setdefault("landing_date", dt.date(2028, 1, 1))
    st.session_state.setdefault("landing_time", dt.time(0, 0))
    st.session_state.setdefault("window_days", 14)
    st.session_state.setdefault("selected_site", None)


def landing_dt() -> dt.datetime:
    return dt.datetime.combine(st.session_state.landing_date, st.session_state.landing_time)


def fmt_hours(hours, up_now: bool, what: str) -> str:
    """Hours until a body sets, as text."""
    if hours is None or (isinstance(hours, float) and math.isnan(hours)):
        return "stays up"
    if not up_now or hours <= 0:
        return f"{what} hidden at landing"
    days, rem = divmod(int(round(hours)), 24)
    return f"{days} d {rem} h" if days else f"{rem} h"


def dark_layout(fig: go.Figure, height: int) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(color="#cbd5e1"), legend=dict(orientation="h", y=1.08, x=0),
    )
    return fig


# ------------------------------------------------------------------ step 1


def page_date() -> None:
    st.title("Lunar Landing Optimal System")
    st.caption("Choose when to land at the Moon's south pole, then see which sites work on that date.")

    left, _ = st.columns([2, 1])
    with left:
        st.header("Step 1 of 2: When do you plan to land?")
        c1, c2 = st.columns(2)
        st.session_state.landing_date = c1.date_input(
            "Planned landing date (UTC)", value=st.session_state.landing_date,
            min_value=FIRST_DAY, max_value=LAST_DAY,
        )
        st.session_state.landing_time = c2.time_input(
            "Landing time (UTC)", value=st.session_state.landing_time, step=3600
        )
        st.session_state.window_days = st.slider(
            "Mission length on the surface (days)", 1, 60, st.session_state.window_days,
            help="Sunlight and Earth contact are assessed over this period after landing.",
        )
        st.write(
            f"Landing **{landing_dt():%d %b %Y, %H:%M} UTC**, "
            f"operating for **{st.session_state.window_days} days**."
        )
        if st.button("Find landing sites", type="primary"):
            st.session_state.step = 2
            st.rerun()

    with st.expander("Why does the date matter so much?"):
        st.write(
            "At the Moon's south pole the Sun and the Earth both stay within a few degrees of the "
            "horizon. A ridge a few kilometres away can hide either of them for days. Whether a site "
            "has power (Sun) and a radio link (Earth) therefore depends strongly on the date."
        )


# ------------------------------------------------------------------ charts


def polar_map(ranked: pd.DataFrame, selected: str) -> go.Figure:
    fig = go.Figure()
    max_r = 2 * MOON_RADIUS_M * math.tan(math.radians(6.0) / 2) / 1000.0  # 84 deg S
    for lat in (-89, -88, -87, -86, -85, -84):
        r = 2 * MOON_RADIUS_M * math.tan(math.radians(90 + lat) / 2) / 1000.0
        ang = np.radians(np.arange(0, 361, 3))
        fig.add_trace(go.Scatter(x=r * np.sin(ang), y=r * np.cos(ang), mode="lines",
                                 line=dict(color="#2c3a4d", width=1), hoverinfo="skip", showlegend=False))
        fig.add_annotation(x=0, y=-r, text=f"{-lat}°S", showarrow=False, yshift=-8,
                           font=dict(color="#7b8794", size=10))
    for lon in range(0, 360, 30):
        a = math.radians(lon)
        fig.add_trace(go.Scatter(x=[0, max_r * math.sin(a)], y=[0, max_r * math.cos(a)], mode="lines",
                                 line=dict(color="#2c3a4d", width=1), hoverinfo="skip", showlegend=False))
    for text, x, y, xs, ys in (("0° (towards Earth)", 0, max_r, 0, 12), ("90°E", max_r, 0, 22, 0),
                               ("90°W", -max_r, 0, -22, 0), ("180°", 0, -max_r, 0, -22)):
        fig.add_annotation(x=x, y=y, text=text, showarrow=False, xshift=xs, yshift=ys,
                           font=dict(color="#cbd5e1", size=11))

    colours = [PICK if r.site == selected else (PASS if r.passes else FAIL) for r in ranked.itertuples()]
    fig.add_trace(go.Scatter(
        x=ranked["x_km"], y=ranked["y_km"], mode="markers+text",
        text=[str(v) for v in ranked["rank"]], textfont=dict(color="white", size=11),
        marker=dict(size=24, color=colours, line=dict(color="white", width=1)),
        customdata=np.stack([ranked["site"], ranked["sun_window"], ranked["earth_window"],
                             ranked["slope_mean_deg"], ranked["score"]], axis=-1),
        hovertemplate=("<b>%{customdata[0]}</b><br>Sunlight in mission: %{customdata[1]:.0%}<br>"
                       "Earth contact in mission: %{customdata[2]:.0%}<br>Mean slope: %{customdata[3]:.1f}°<br>"
                       "Score: %{customdata[4]:.2f}<extra></extra>"),
        showlegend=False,
    ))
    pad = max_r * 1.15
    dark_layout(fig, 600)
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), dragmode=False,
                      xaxis=dict(visible=False, range=[-pad, pad]),
                      yaxis=dict(visible=False, range=[-pad, pad], scaleanchor="x", scaleratio=1))
    return fig


def panorama(lookup: planner.Lookup, site: str, tl: pd.DataFrame) -> go.Figure:
    """Terrain skyline all around the site with the Sun's and Earth's paths over the mission."""
    sk = planner.skyline(lookup, site)
    floor = min(sk["terrain_el_deg"].min(), tl["sun_el"].min(), tl["earth_el"].min()) - 1.0
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sk["azimuth_deg"], y=[floor] * len(sk), mode="lines",
                             line=dict(width=0), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=sk["azimuth_deg"], y=sk["terrain_el_deg"], mode="lines", fill="tonexty",
                             line=dict(color="#93a1b5", width=1.5), fillcolor=GROUND, name="Terrain skyline",
                             hovertemplate="Azimuth %{x}°<br>Skyline %{y:.2f}°<extra></extra>"))
    for body, colour, label in (("sun", SUN, "Sun"), ("earth", EARTH, "Earth")):
        up = tl[f"{body}_up"]
        for visible, opacity, suffix in ((True, 1.0, "visible"), (False, 0.25, "hidden")):
            part = tl[up == visible]
            fig.add_trace(go.Scatter(
                x=part[f"{body}_az"], y=part[f"{body}_el"], mode="markers",
                marker=dict(color=colour, size=5, opacity=opacity), name=f"{label}, {suffix}",
                customdata=part["time_utc"].dt.strftime("%d %b %H:%M"),
                hovertemplate=label + " %{customdata} UTC<br>Azimuth %{x:.1f}°, elevation %{y:.2f}°<extra></extra>"))
        fig.add_trace(go.Scatter(
            x=[tl[f"{body}_az"].iloc[0]], y=[tl[f"{body}_el"].iloc[0]], mode="markers",
            marker=dict(color=colour, size=16, symbol="circle-open", line=dict(width=3, color=colour)),
            name=f"{label} at landing", hoverinfo="skip"))
    dark_layout(fig, 380)
    fig.update_xaxes(title="Direction (azimuth, clockwise from lunar north)", range=[0, 360],
                     tickvals=[0, 90, 180, 270, 360], ticktext=["N 0°", "E 90°", "S 180°", "W 270°", "N 360°"],
                     gridcolor="#1f2a3a")
    fig.update_yaxes(title="Elevation (degrees)", gridcolor="#1f2a3a", zerolinecolor="#55647a")
    return fig


def margin_chart(tl: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for body, colour, label in (("sun", SUN, "Sun"), ("earth", EARTH, "Earth")):
        fig.add_trace(go.Scatter(x=tl["time_utc"], y=tl[f"{body}_margin"], mode="lines",
                                 line=dict(color=colour, width=2), name=label,
                                 hovertemplate=label + " %{x|%d %b %H:%M} UTC<br>%{y:.2f}° above skyline<extra></extra>"))
    fig.add_hline(y=0, line=dict(color="#e2e8f0", width=1, dash="dash"))
    ecl = tl[tl["eclipse"] > 0]
    if len(ecl):
        fig.add_vrect(x0=ecl["time_utc"].iloc[0], x1=ecl["time_utc"].iloc[-1], fillcolor="#e63946",
                      opacity=0.25, line_width=0, annotation_text="eclipse", annotation_position="top left")
    dark_layout(fig, 300)
    fig.update_xaxes(title="Time (UTC)", gridcolor="#1f2a3a")
    fig.update_yaxes(title="Degrees above the terrain skyline", gridcolor="#1f2a3a")
    return fig


def date_heatmap(scan: pd.DataFrame, order: list[str], landing_day: dt.date, column: str, title: str) -> go.Figure:
    grid = scan.pivot(index="site", columns="date", values=column).loc[order]
    fig = go.Figure(go.Heatmap(
        z=grid.values, x=[pd.Timestamp(d) for d in grid.columns], y=grid.index, zmin=0, zmax=1,
        colorscale=[[0, "#1b2433"], [0.5, "#3b6ea5"], [0.95, "#8fd3c8"], [1, "#f6f7b0"]],
        colorbar=dict(title="share", tickformat=".0%"),
        hovertemplate="%{y}<br>Landing %{x|%d %b %Y}<br>" + title + ": %{z:.0%}<extra></extra>"))
    if grid.columns[0] <= landing_day <= grid.columns[-1]:
        fig.add_vline(x=pd.Timestamp(landing_day), line=dict(color=PICK, width=2))
    dark_layout(fig, 430)
    fig.update_layout(title=dict(text=title, font=dict(color="#e2e8f0", size=15)), margin=dict(l=10, r=10, t=45, b=10))
    return fig


# ------------------------------------------------------------------ step 2


def limit_args(limits: dict) -> dict:
    """The subset of settings that the calendar functions accept."""
    return {k: v for k, v in limits.items() if k not in ("slip_days", "weights")}


def site_panel(lookup: planner.Lookup, ranked: pd.DataFrame, limits: dict) -> None:
    names = list(ranked["site"])
    if st.session_state.selected_site not in names:
        st.session_state.selected_site = names[0]
    site = st.selectbox("Site", names, index=names.index(st.session_state.selected_site))
    st.session_state.selected_site = site
    row = next(r for r in ranked.itertuples() if r.site == site)
    window = st.session_state.window_days

    st.subheader(f"#{row.rank}  {row.site}")
    st.caption(f"{abs(row.lat):.3f}°S, {abs(row.lon):.3f}°{'E' if row.lon >= 0 else 'W'} · "
               f"surface height {row.height_m:,.0f} m")
    if row.passes:
        st.success(f"Passes every limit. Score {row.score:.2f}.")
    else:
        st.warning("Not recommended on this date: " + row.fail_reasons + ".")

    def short(hours, up_now, what):
        return fmt_hours(hours, up_now, what).replace(" d ", "d ").replace(" h", "h").replace(f"{what} hidden at landing", "hidden")

    c1, c2, c3 = st.columns(3)
    c1.metric("Sunlight", f"{row.sun_window:.0%}",
              help="Share of the mission with any part of the Sun above the terrain skyline.")
    c2.metric("Earth contact", f"{row.earth_window:.0%}",
              help="Share of the mission with any part of Earth above the terrain skyline.")
    c3.metric("Mean slope", f"{row.slope_mean_deg:.1f}°", help=f"Within 120 m. Steepest point: {row.slope_max_deg:.1f}°.")
    c1.metric("Sunset in", short(row.hours_to_sunset, row.sun_up_at_landing, "Sun"),
              help="Time from landing until the Sun next goes behind terrain. 'hidden' means it is already hidden at landing.")
    c2.metric("Earthset in", short(row.hours_to_earthset, row.earth_up_at_landing, "Earth"),
              help="Time from landing until Earth next goes behind terrain.")
    c3.metric("Sun height", f"{row.sun_el_at_landing:+.1f}°", help="Sun elevation at landing, relative to a level horizon.")
    c1.metric("Longest dark", f"{row.longest_dark_h:.0f}h", help="Longest unbroken period without sunlight in the mission.")
    c2.metric("Longest blackout", f"{row.longest_blackout_h:.0f}h", help="Longest unbroken period without Earth in view.")
    c3.metric("Steepest", f"{row.slope_max_deg:.1f}°", help="Steepest slope within 120 m of the site.")
    st.caption(f"Long-term averages (NASA LOLA, 18.6 years): sunlight {row.sun_long_term:.0%}, "
               f"Earth visibility {row.earth_long_term:.0%}.")

    slip = limits["slip_days"]
    if slip:
        st.markdown(
            f"**If the landing slips by up to {slip} days:** sunlight could fall to "
            f"**{row.sun_window_worst:.0%}** and Earth contact to **{row.earth_window_worst:.0%}**. "
            + ("The site would still meet the mission limits." if row.stable
               else "The site would no longer meet the mission limits.")
        )
    if row.eclipse_hours > 0:
        st.markdown(f"**Lunar eclipse:** Earth blocks part or all of the Sun for about {row.eclipse_hours:.0f} h "
                    "during the mission. This is not subtracted from the sunlight figure.")

    near = planner.nearest_passing_dates(lookup, landing_dt(), window, **limit_args(limits))
    near = near.set_index("site").loc[site]
    if not near["passes_on_date"]:
        options = [d for d in (near["previous_date"], near["next_date"]) if d is not None and not pd.isna(d)]
        if options:
            st.markdown("**Nearest landing dates on which this site passes:** "
                        + " and ".join(f"{d:%d %b %Y}" for d in options) + ".")
        else:
            st.markdown("**This site does not pass these limits on any date in 2027-2030.**")


def page_sites() -> None:
    lookup = get_lookup()
    window = st.session_state.window_days
    left, right = st.columns([4, 1])
    left.header("Step 2 of 2: Choose a landing site")
    left.caption(f"Landing {landing_dt():%d %b %Y, %H:%M} UTC · {window} days on the surface")
    if right.button("Change date"):
        st.session_state.step = 1
        st.rerun()

    with st.sidebar:
        st.subheader("Limits")
        limits = dict(
            min_sun_window=st.slider("Minimum sunlight in mission", 0, 100, 95, 5, format="%d%%") / 100,
            min_earth_window=st.slider("Minimum Earth contact in mission", 0, 100, 95, 5, format="%d%%") / 100,
            max_slope_deg=float(st.slider("Maximum mean slope", 1, 20, 10, format="%d°")),
            min_sun_long_term=st.slider("Minimum long-term sunlight", 0, 85, 50, 5, format="%d%%") / 100,
            min_earth_long_term=st.slider("Minimum long-term Earth visibility", 0, 100, 50, 5, format="%d%%") / 100,
            slip_days=st.slider("Possible landing slip (days either way)", 0, 30, 14),
        )
        st.subheader("Weights")
        limits["weights"] = {
            "sunlight": st.slider("Sunlight", 0.0, 3.0, 1.0, 0.5),
            "earth": st.slider("Earth contact", 0.0, 3.0, 1.0, 0.5),
            "flatness": st.slider("Flatness", 0.0, 3.0, 1.0, 0.5),
        }
        if sum(limits["weights"].values()) == 0:
            st.warning("All weights are zero; using equal weights.")
            limits["weights"] = None

    ranked = planner.rank_for_date(lookup, landing_dt(), window, **limits)
    passing = int(ranked["passes"].sum())
    if passing:
        st.write(f"**{passing} of {len(ranked)}** candidate sites pass every limit on this date.")
    else:
        near = planner.nearest_passing_dates(lookup, landing_dt(), window, **limit_args(limits))
        near = near.dropna(subset=["days_to_nearest"]).sort_values("days_to_nearest")
        if len(near):
            best = near.iloc[0]
            dates = [d for d in (best["previous_date"], best["next_date"]) if d is not None and not pd.isna(d)]
            closest = min(dates, key=lambda d: abs((d - landing_dt().date()).days))
            st.error(f"No site passes every limit on this date. The nearest option is **{best['site']}** "
                     f"with a landing on **{closest:%d %b %Y}** ({int(best['days_to_nearest'])} days away).")
        else:
            st.error("No site passes these limits on any date in 2027-2030. Loosen a limit in the sidebar.")

    tab_sites, tab_dates, tab_custom = st.tabs(["Sites", "Compare dates", "Custom coordinates"])

    with tab_sites:
        map_col, info_col = st.columns([5, 4])
        with info_col:
            site_panel(lookup, ranked, limits)
        with map_col:
            st.plotly_chart(polar_map(ranked, st.session_state.selected_site), width="stretch",
                            config={"displayModeBar": False, "scrollZoom": False})
            st.caption("Lunar south pole, 84°S to the pole. Numbers are ranks; grey sites fail a limit; "
                       "the selected site is orange.")

        site = st.session_state.selected_site
        tl = planner.timeline(lookup, site, landing_dt(), window)
        st.subheader(f"Sky at {site} during the mission")
        st.plotly_chart(panorama(lookup, site, tl), width="stretch", config={"displayModeBar": False})
        st.caption("The grey shape is the terrain skyline in every direction. Each dot is the Sun or Earth "
                   "one hour apart; faint dots are hidden behind terrain. Rings mark the moment of landing.")
        st.plotly_chart(margin_chart(tl), width="stretch", config={"displayModeBar": False})
        st.caption("Above the dashed line the body is visible; below it terrain hides it. " + ESTIMATE_NOTE)

        st.subheader("All candidate sites")
        table = ranked[["rank", "site", "score", "sun_window", "earth_window", "slope_mean_deg",
                        "sun_window_worst", "earth_window_worst", "passes", "fail_reasons"]].rename(columns={
            "rank": "Rank", "site": "Site", "score": "Score", "sun_window": "Sunlight",
            "earth_window": "Earth contact", "slope_mean_deg": "Slope (°)",
            "sun_window_worst": "Sunlight if slipped", "earth_window_worst": "Contact if slipped",
            "passes": "Passes", "fail_reasons": "Why not"})
        bar = dict(format="percent", min_value=0, max_value=1)
        st.dataframe(table, hide_index=True, width="stretch", column_config={
            "Score": st.column_config.NumberColumn(format="%.2f"),
            "Sunlight": st.column_config.ProgressColumn(**bar),
            "Earth contact": st.column_config.ProgressColumn(**bar),
            "Sunlight if slipped": st.column_config.ProgressColumn(**bar),
            "Contact if slipped": st.column_config.ProgressColumn(**bar),
            "Slope (°)": st.column_config.NumberColumn(format="%.1f"),
        })

    with tab_dates:
        st.write("How each site would do for the same mission length on every landing date. "
                 "The orange line is the chosen date.")
        years = [2027, 2028, 2029, 2030]
        year = st.radio("Year", years, horizontal=True, index=years.index(landing_dt().year))
        scan = planner.date_scan(lookup, window, hour_utc=landing_dt().hour)
        scan = scan[[d.year == year for d in scan["date"]]].copy()
        scan["both"] = scan[["sun_window", "earth_window"]].min(axis=1)
        order = list(ranked["site"])[::-1]
        st.plotly_chart(date_heatmap(scan, order, landing_dt().date(), "both",
                                     "Lower of sunlight and Earth contact"), width="stretch")
        c1, c2 = st.columns(2)
        c1.plotly_chart(date_heatmap(scan, order, landing_dt().date(), "sun_window", "Sunlight in mission"),
                        width="stretch")
        c2.plotly_chart(date_heatmap(scan, order, landing_dt().date(), "earth_window", "Earth contact in mission"),
                        width="stretch")
        best = planner.best_dates(lookup, st.session_state.selected_site, window)
        st.write(f"**Best landing dates for {st.session_state.selected_site}, 2027-2030:** "
                 + ", ".join(f"{d:%d %b %Y}" for d in best["date"]) + ".")
        st.caption(ESTIMATE_NOTE)

    with tab_custom:
        st.write("Check any point on the Moon for the same landing date and mission length.")
        c1, c2 = st.columns(2)
        lat = c1.number_input("Latitude (degrees, south is negative)", -90.0, 90.0, -89.5, 0.1, format="%.3f")
        lon = c2.number_input("East longitude (degrees, west is negative)", -180.0, 360.0, 0.0, 0.5, format="%.3f")
        summary, ctl = planner.custom_site(lat, lon, landing_dt(), window)
        st.warning("Flat-horizon estimate, terrain not included. Real terrain hides the Sun and Earth more "
                   "often, so these figures are optimistic. Slope is not available for custom points.")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Sunlight in mission", f"{summary['sun_window']:.0%}")
        m2.metric("Earth contact in mission", f"{summary['earth_window']:.0%}")
        m3.metric("Time to sunset", fmt_hours(summary["hours_to_sunset"], bool(ctl["sun_up"].iloc[0]), "Sun"))
        m4.metric("Time to Earthset", fmt_hours(summary["hours_to_earthset"], bool(ctl["earth_up"].iloc[0]), "Earth"))
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=ctl["time_utc"], y=ctl["sun_el"], line=dict(color=SUN, width=2), name="Sun"))
        fig.add_trace(go.Scatter(x=ctl["time_utc"], y=ctl["earth_el"], line=dict(color=EARTH, width=2), name="Earth"))
        fig.add_hline(y=0, line=dict(color="#e2e8f0", width=1, dash="dash"))
        dark_layout(fig, 320)
        fig.update_xaxes(title="Time (UTC)", gridcolor="#1f2a3a")
        fig.update_yaxes(title="Elevation above a level horizon (degrees)", gridcolor="#1f2a3a")
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    st.caption("Data: NASA LRO LOLA visibility maps and elevation models (PDS Geosciences Node), Artemis III "
               "candidate regions (Moon Trek). Sun and Earth positions checked against NASA JPL Horizons.")


init_state()
if st.session_state.step == 1:
    page_date()
else:
    page_sites()
