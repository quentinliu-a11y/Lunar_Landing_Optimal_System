# AI-generated interface redesign by OpenAI Codex, based on Claude's working interface.
# Reviewed and adjusted by Claude (Anthropic), 2026-11-15: label legibility, heat-map margins, slip result shown directly.
# Visual redesign by Claude (Anthropic), 2026-11-15: dark "night side" theme, Sun amber / Earth blue throughout,
# site read-out with bars that mark the worst case if the landing slips. AI-generated.
"""Lunar Landing Optimal System - polar atlas interface.

AI-assisted: written by Claude (Anthropic), 2026-11-14.

Flow: step 1 pick a planned landing date, step 2 see the candidate sites
ranked for that date, open one, compare dates, or try custom coordinates.

All numbers come from src/planner.py; nothing is calculated here.

Run with:  streamlit run src/app.py
"""

from __future__ import annotations

import datetime as dt
import math
import base64
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import warnings

import erfa
import groundlink
import planner
from sites import MOON_RADIUS_M, load_sites, rank_sites

st.set_page_config(page_title="Lunar Landing | South Pole Atlas", layout="wide",
                   initial_sidebar_state="collapsed")

FIRST_DAY, LAST_DAY = dt.date(2027, 1, 1), dt.date(2030, 12, 31)
PASS, FAIL, PICK = "#6fcf97", "#6b747c", "#ff7a45"
SUN, EARTH, GROUND = "#f0a43a", "#5aa9e6", "#1b2229"
BG, PANEL, RULE, INK, MUTED = "#0b0e11", "#141a20", "#27303a", "#e8e6df", "#8c959c"
IMAGERY_CREDIT = "NASA/GSFC/Arizona State University · LROC WAC mosaic via NASA Moon Trek"
IMAGERY_URL = "https://trek.nasa.gov/moon/trekarcgis/rest/services/LRO_WAC_Mosaic_SPole60_100m_v02/ImageServer"
ESTIMATE_NOTE = (
    "Estimate anchored to NASA long-term data. "
    "LOLA terrain skylines are calibrated to NASA's 18.6-year visibility averages."
)


def styles() -> None:
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap');
    :root {color-scheme:dark; --bg:#0b0e11; --panel:#141a20; --rule:#27303a; --ink:#e8e6df; --muted:#8c959c;
        --sun:#f0a43a; --earth:#5aa9e6; --pass:#6fcf97; --pick:#ff7a45;
        --sans:'Space Grotesk','Segoe UI',Arial,sans-serif; --mono:'IBM Plex Mono',Consolas,monospace;}
    .stApp {background:var(--bg); color:var(--ink); font-family:var(--sans);}
    [data-testid="stHeader"] {background:transparent;}
    [data-testid="stMainBlockContainer"], .main .block-container {max-width:1480px; padding:2rem 3.5rem 3rem;}
    [data-testid="stSidebar"] {background:var(--panel); border-right:1px solid var(--rule);}
    h1,h2,h3,h1 span,h2 span,h3 span {font-family:var(--sans)!important; color:var(--ink);}
    p,label,li {font-family:var(--sans); color:var(--ink);}
    h1 {font-weight:500!important; letter-spacing:-.04em; font-size:clamp(2.6rem,5vw,4.6rem)!important; line-height:1.02!important;}
    h2 {font-size:2rem!important; font-weight:500!important; letter-spacing:-.03em;}
    h3 {font-size:1.35rem!important; font-weight:500!important; letter-spacing:-.01em;}
    [data-testid="stCaptionContainer"] p {color:var(--muted); font-size:.8rem; line-height:1.5;}
    .masthead {display:flex; justify-content:space-between; align-items:center; gap:1rem;
        padding:0 0 1rem; margin-bottom:1.6rem; border-bottom:1px solid var(--rule);}
    .wordmark {font-weight:700; letter-spacing:.16em; font-size:.84rem;}
    .wordmark i {display:inline-block; width:.62rem; height:.62rem; border-radius:50%; margin-right:.6rem;
        background:linear-gradient(90deg,var(--ink) 50%,#39424b 50%); vertical-align:-1px;}
    .masthead small,.eyebrow,.atlas-heading {font-family:var(--mono); text-transform:uppercase;
        font-size:.7rem; letter-spacing:.14em; color:var(--muted);}
    .eyebrow {margin:0 0 .8rem; color:var(--sun);}
    .deck {max-width:32rem; font-size:1.05rem; line-height:1.6; color:var(--muted); margin:1rem 0 1.6rem;}
    .atlas-heading {display:flex; justify-content:space-between; border-top:1px solid var(--rule); padding-top:.8rem; margin:.5rem 0;}
    .legend {display:flex; flex-wrap:wrap; gap:1.2rem; font-size:.8rem; color:var(--muted); margin:.6rem 0;}
    .legend b {font-size:1rem; margin-right:.3rem;}
    .result-line {padding:.7rem 0; border-bottom:1px solid var(--rule); color:var(--muted);}
    .result-line strong {color:var(--ink); font-family:var(--mono); font-weight:500;}
    .verdict {font-family:var(--mono); font-size:.78rem; letter-spacing:.08em; text-transform:uppercase;
        padding:.55rem .8rem; border-left:3px solid var(--pass); background:var(--panel); color:var(--ink); margin:.4rem 0 1.1rem;}
    .verdict.no {border-left-color:var(--pick);}
    .gauge {margin:0 0 1.15rem;}
    .g-top {display:flex; justify-content:space-between; align-items:baseline;}
    .g-label {font-family:var(--mono); font-size:.72rem; letter-spacing:.14em; text-transform:uppercase; color:var(--muted);}
    .g-val {font-family:var(--mono); font-size:2.5rem; font-weight:500; letter-spacing:-.04em; line-height:1.1;}
    .g-bar {position:relative; height:10px; background:#1d252d; margin:.35rem 0 .4rem;}
    .g-bar i {position:absolute; inset:0 auto 0 0; display:block;}
    .g-bar b {position:absolute; top:-5px; bottom:-5px; width:2px; background:var(--ink);}
    .g-bar u {position:absolute; top:0; bottom:0; width:1px; background:var(--muted); opacity:.7;}
    .g-note {font-size:.8rem; color:var(--muted);} .g-note em {font-style:normal; color:var(--ink); font-family:var(--mono);}
    .stats {display:grid; grid-template-columns:repeat(4,1fr); border-top:1px solid var(--rule); border-bottom:1px solid var(--rule); margin:.2rem 0 1rem;}
    .stats.datascale {grid-template-columns:repeat(5,1fr);} .stats.datascale span {color:var(--sun);}
    .stats div {padding:.7rem .6rem .7rem 0;} .stats div+div {padding-left:.8rem; border-left:1px solid var(--rule);}
    .stats small {display:block; font-family:var(--mono); font-size:.66rem; letter-spacing:.12em; text-transform:uppercase; color:var(--muted);}
    .stats span {font-family:var(--mono); font-size:1.2rem;}
    [data-testid="stForm"] {border:1px solid var(--rule); border-radius:2px; padding:1.25rem; background:var(--panel);}
    [data-testid="stMetric"] {border-top:1px solid var(--rule); padding:.8rem 0 .2rem;}
    [data-testid="stMetricLabel"] p {font-family:var(--mono); font-size:.7rem; letter-spacing:.1em; text-transform:uppercase; color:var(--muted);}
    [data-testid="stMetricValue"] {font-family:var(--mono); font-size:1.7rem; letter-spacing:-.03em; color:var(--ink);}
    [data-testid="stButton"] button,[data-testid="stFormSubmitButton"] button {
        border-radius:2px; min-height:2.8rem; font-family:var(--mono); letter-spacing:.06em;
        transition:transform 140ms ease-out,opacity 140ms ease-out;}
    button[kind^="primary"] {background:var(--sun)!important; border-color:var(--sun)!important;}
    button[kind^="primary"] p {color:#14100a!important; font-weight:500;}
    button[kind="secondary"] {background:transparent; color:var(--ink); border-color:#46525e;}
    button:active {transform:scale(.985);}
    button:focus-visible,input:focus-visible {outline:2px solid var(--sun)!important; outline-offset:3px;}
    [data-testid="stRadio"] [role="radiogroup"] {gap:.3rem; padding:.3rem 0 .8rem; border-bottom:1px solid var(--rule);}
    [data-testid="stRadio"] label {padding:.45rem .7rem; border-radius:2px;}
    [data-testid="stRadio"] label:has(input:checked) {background:#1d252d;}
    [data-testid="stAlert"],[data-testid="stExpander"] {border-radius:2px;}
    @media (hover:hover) and (pointer:fine) {button:hover {opacity:.86;}}
    @media (prefers-reduced-motion:reduce) {*,*::before,*::after {
        animation:none!important; transition:none!important; scroll-behavior:auto!important;}}
    @media (max-width:760px) {
        [data-testid="stMainBlockContainer"],.main .block-container {padding:4rem 1rem 2rem;}
        .masthead {align-items:flex-start;} .masthead small {max-width:9rem;text-align:right;}
        h1 {font-size:2.8rem!important;} h2 {font-size:1.7rem!important;}
        .stats {grid-template-columns:repeat(2,1fr);} .g-val {font-size:2rem;}
    }
    </style>""", unsafe_allow_html=True)


def gauge(label: str, colour: str, value: float, worst: float | None, slip: int, limit: float) -> str:
    """One read-out bar. Values come from the planner; this only draws them."""
    mark = note = ""
    if slip and worst is not None:
        mark = f'<b style="left:calc({worst:.1%} - 1px)"></b>'
        note = f'<div class="g-note">Worst case if the landing slips ±{slip} days: <em>{worst:.0%}</em></div>'
    return (f'<div class="gauge"><div class="g-top"><span class="g-label">{label}</span>'
            f'<span class="g-val" style="color:{colour}">{value:.0%}</span></div>'
            f'<div class="g-bar"><i style="width:{value:.1%};background:{colour}"></i>'
            f'<u style="left:{limit:.1%}" title="Your limit"></u>{mark}</div>{note}</div>')


PAGES = "https://quentinliu-a11y.github.io/Lunar_Landing_Optimal_System/"
SIM_PAGE = PAGES + "Lunar%20Landing%20Site%20Simulator%20(1).html"
REPO = "https://github.com/quentinliu-a11y/Lunar_Landing_Optimal_System"
LANDERS = {"Nova-C class · robotic, slopes ≤ 10°": 10, "Crewed lander · Starship HLS, tilt ≤ 8°": 8, "Custom limit": None}


def masthead() -> None:
    st.markdown('<div class="masthead"><span class="wordmark"><i></i>LUNAR LANDING NAVIGATOR</span>'
                f'<small><a href="{PAGES}" target="_blank">Guided tour</a> · '
                f'<a href="{SIM_PAGE}" target="_blank">3D site view</a> · '
                f'<a href="{REPO}" target="_blank">Code &amp; data</a></small></div>', unsafe_allow_html=True)


def sim_link(site: str, start: dt.date, days: int) -> str:
    from urllib.parse import quote
    return f"{SIM_PAGE}?site={quote(site)}&start={start:%Y-%m-%d}&days={days}"


@st.cache_data(show_spinner=False)
def overview_sites() -> pd.DataFrame:
    return rank_sites(load_sites(), min_sun=0.5, min_earth=0.5)


@st.cache_data(show_spinner=False)
def lunar_imagery() -> str | None:
    """Display-only image: no runtime downloads or image-derived science.

    Moon Trek export extent: x/y +/-210000 m, south polar stereographic,
    radius 1737400 m, central meridian 0, standard parallel -90.
    Matches sites.py's +y toward 0 longitude and +x toward 90 E.
    Pixel edges, not pixel centres, define Plotly image bounds.
    """
    image_path = Path(__file__).resolve().parents[1] / "data/lroc-south-pole.jpg"
    if not image_path.is_file():
        return None
    return "data:image/jpeg;base64," + base64.b64encode(image_path.read_bytes()).decode("ascii")


@st.cache_data(show_spinner=False, max_entries=96)
def query(method: str, *args, **kwargs):
    """Cache planner results by their full input settings; never reimplement science here."""
    return getattr(planner, method)(get_lookup(), *args, **kwargs)


@st.cache_data(show_spinner=False, max_entries=32)
def custom_conditions(lat: float, lon: float, landing: dt.datetime, window: int):
    return planner.custom_site(lat, lon, landing, window)


@st.cache_resource(show_spinner="Computing Sun and Earth positions for 2027-2030...")
def get_lookup() -> planner.Lookup:
    return planner.build_lookup(FIRST_DAY, LAST_DAY)


@st.cache_resource(show_spinner=False)
def dsn_elevation() -> np.ndarray:
    """(3, T) Moon elevation at the three DSN complexes for every lookup hour."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", erfa.ErfaWarning)   # future UTC: leap seconds not yet announced
        return groundlink.moon_elevation(get_lookup().times)


def ground_link(site: str, landing: dt.datetime, window: int) -> dict:
    lk = get_lookup()
    k = list(lk.sites["site"]).index(site)
    i = planner._index(lk, landing)
    j = i + window * 24 + 1
    months = lk.times[i:j].astype("datetime64[M]").astype(int) % 12 + 1
    return groundlink.link_summary(dsn_elevation()[:, i:j], months, lk.earth_up[k, i:j])


def init_state() -> None:
    st.session_state.setdefault("step", 1)
    st.session_state.setdefault("landing_date", dt.date(2028, 1, 1))
    st.session_state.setdefault("landing_time", dt.time(0, 0))
    st.session_state.setdefault("window_days", 14)
    st.session_state.setdefault("selected_site", None)
    st.session_state.setdefault("lander_idx", 0)
    # Retain these widget values when a different page/section is mounted.
    for key in list(st.session_state):
        if key.startswith(("criterion_", "custom_", "hour_")):
            st.session_state[key] = st.session_state[key]


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
        height=height, margin=dict(l=75, r=20, t=55, b=55), paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(color="#b7bec4", family="Space Grotesk, Segoe UI, Arial, sans-serif", size=12),
        legend=dict(orientation="h", y=1.16, x=0),
        hoverlabel=dict(bgcolor=PANEL, font_color=INK, bordercolor=RULE),
        transition=dict(duration=0),
    )
    return fig


# ------------------------------------------------------------------ step 1


def page_date() -> None:
    left, right = st.columns([1, 1.12], gap="large")
    with left:
        st.markdown('<p class="eyebrow">01 / Mission window</p>', unsafe_allow_html=True)
        st.title("Choose your landing window.")
        st.markdown('<p class="deck">At the lunar south pole, a small shift in date changes '
                    'the picture. Find a place with sunlight, Earth contact and suitable terrain '
                    'for your mission.</p>', unsafe_allow_html=True)
        with st.form("mission"):
            c1, c2 = st.columns(2)
            date = c1.date_input("Planned landing date (UTC)", value=st.session_state.landing_date,
                                 min_value=FIRST_DAY, max_value=LAST_DAY)
            time = c2.time_input("Landing time (UTC)", value=st.session_state.landing_time, step=3600)
            window = st.slider("Mission length on the surface (days)", 1, 60, st.session_state.window_days,
                               help="Visibility is assessed over this period after landing.")
            lander = st.radio("Your lander", list(LANDERS), index=st.session_state.lander_idx,
                              help="Nova-C: IM-1 design limit. Crewed: NASA's tilt limit for its human landers "
                                   "(NASA OIG IG-26-004). Compared with each site's mean slope over 120 m (NASA LOLA).")
            custom_slope = st.number_input("Custom maximum slope (degrees, used with Custom limit)", 1, 20,
                                           int(st.session_state.get("criterion_slope", 10)))
            st.caption("2027–2030 · UTC throughout · Hourly estimates")
            submitted = st.form_submit_button("Find landing sites →", type="primary", width="stretch")
            if submitted:
                if date is None or time is None:
                    st.error("Enter a landing date and time to continue.")
                else:
                    idx = list(LANDERS).index(lander)
                    if idx != st.session_state.lander_idx or (LANDERS[lander] is None and custom_slope != st.session_state.get("custom_slope_used")):
                        # Only a changed lander choice resets the slope limit; a limit set in the sidebar is kept otherwise.
                        st.session_state.criterion_slope = int(LANDERS[lander] or custom_slope)
                        st.session_state.custom_slope_used = custom_slope
                    st.session_state.update(landing_date=date, landing_time=time, window_days=window, step=2, lander_idx=idx)
                    st.rerun()
        with st.expander("Why the landing date matters"):
            st.write("The Sun and Earth graze the polar horizon. A nearby ridge can hide either for days. "
                     "We compare your mission window against each site's terrain skyline and visibility history.")
    with right:
        sites = overview_sites()
        st.markdown(f'<div class="atlas-heading"><span>POLAR ATLAS</span><span>{len(sites)} CANDIDATE REGIONS</span></div>',
                    unsafe_allow_html=True)
        st.plotly_chart(polar_map(sites, "", overview=True), width="stretch",
                        config={"displayModeBar": False, "scrollZoom": False}, theme=None)
        st.caption("Artemis III candidate regions · NASA LOLA coordinates. Mission rankings follow your date selection.")
        image_credit()
        st.markdown('<div class="atlas-heading"><span>01 / SET A DATE</span><span>02 / EXPLORE SITES</span></div>',
                    unsafe_allow_html=True)


# ------------------------------------------------------------------ charts


def polar_map(ranked: pd.DataFrame, selected: str, overview: bool = False) -> go.Figure:
    fig = go.Figure()
    source = lunar_imagery()
    if source:
        fig.add_layout_image(source=source, xref="x", yref="y", x=-210, y=210, sizex=420, sizey=420,
                             sizing="stretch", layer="below", opacity=1, xanchor="left", yanchor="top")
    max_r = 2 * MOON_RADIUS_M * math.tan(math.radians(6.0) / 2) / 1000.0  # 84 deg S
    for lat in (-89, -88, -87, -86, -85, -84):
        r = 2 * MOON_RADIUS_M * math.tan(math.radians(90 + lat) / 2) / 1000.0
        ang = np.radians(np.arange(0, 361, 3))
        fig.add_trace(go.Scatter(x=r * np.sin(ang), y=r * np.cos(ang), mode="lines",
                                 line=dict(color="rgba(211,225,219,.18)", width=1), hoverinfo="skip", showlegend=False))
        fig.add_annotation(x=0, y=-r, text=f"{-lat}°S", showarrow=False, yshift=-8,
                           font=dict(color="#dfe8e1", size=10), bgcolor="rgba(11,14,17,.78)", borderpad=1)
    for lon in range(0, 360, 30):
        a = math.radians(lon)
        fig.add_trace(go.Scatter(x=[0, max_r * math.sin(a)], y=[0, max_r * math.cos(a)], mode="lines",
                                 line=dict(color="rgba(211,225,219,.18)", width=1), hoverinfo="skip", showlegend=False))
    for text, x, y, xs, ys in (("0° (towards Earth)", 0, max_r, 0, 12), ("90°E", max_r, 0, 22, 0),
                               ("90°W", -max_r, 0, -22, 0), ("180°", 0, -max_r, 0, -22)):
        fig.add_annotation(x=x, y=y, text=text, showarrow=False, xshift=xs, yshift=ys,
                           font=dict(color="#f4f4e9", size=11), bgcolor="rgba(11,14,17,.78)", borderpad=2)

    colours = [PICK if r.site == selected else (PASS if r.passes else FAIL) for r in ranked.itertuples()]
    if overview:
        colours = [SUN] * len(ranked)
    custom = ranked[["site"]].values if overview else np.stack(
        [ranked["site"], ranked["sun_window"], ranked["earth_window"], ranked["slope_mean_deg"], ranked["score"]], axis=-1)
    if selected:
        chosen = ranked[ranked.site == selected]
        fig.add_trace(go.Scatter(x=chosen.x_km, y=chosen.y_km, mode="markers", hoverinfo="skip",
                                marker=dict(size=36, color="rgba(0,0,0,0)", line=dict(color=PICK, width=2)),
                                showlegend=False))
    fig.add_trace(go.Scatter(
        x=ranked["x_km"], y=ranked["y_km"], mode="markers",
        text=[str(v) for v in ranked["rank"]], textfont=dict(color="#0e211e", size=11),
        marker=dict(size=8 if overview else 12, color=colours, line=dict(color=BG, width=1.5)),
        customdata=custom,
        hovertemplate="<b>%{customdata[0]}</b><extra></extra>" if overview else ("<b>%{customdata[0]}</b><br>Sunlight in mission: %{customdata[1]:.0%}<br>"
                       "Earth contact in mission: %{customdata[2]:.0%}<br>Mean slope: %{customdata[3]:.1f}°<br>"
                       "Score: %{customdata[4]:.2f}<extra></extra>"),
        showlegend=False,
    ))
    if not overview:
        # Offset only screen-space labels. Actual geographic points never move.
        label_offsets = {
            "de Gerlache Rim 2": (-42, 15), "de Gerlache Rim": (-18, -30),
            "Connecting Ridge Extension": (-38, 30), "Connecting Ridge": (10, 42),
            "Nobile Rim 1": (24, 0), "Leibnitz Beta Plateau": (-25, -18),
        }
        for row, colour in zip(ranked.itertuples(), colours):
            ax, ay = label_offsets.get(row.site, (16, -16))
            fig.add_annotation(x=row.x_km, y=row.y_km, text=str(row.rank), showarrow=True,
                               ax=ax, ay=ay, arrowhead=0, arrowwidth=1, arrowcolor=colour,
                               bgcolor=BG, bordercolor=colour, borderpad=3,
                               font=dict(color="#f4f4e9", size=11), captureevents=False)
    pad = max_r * 1.15
    dark_layout(fig, 520 if overview else 560)
    fig.update_layout(paper_bgcolor=BG, plot_bgcolor=BG, font_color="#cfd5da",
                      margin=dict(l=0, r=0, t=30, b=30), dragmode="pan", clickmode="event+select",
                      uirevision="polar-atlas", selectionrevision=selected,
                      xaxis=dict(visible=False, range=[-pad, pad]),
                      yaxis=dict(visible=False, range=[-pad, pad], scaleanchor="x", scaleratio=1))
    return fig


def image_credit() -> None:
    if lunar_imagery():
        st.caption(f"Imagery: [{IMAGERY_CREDIT}]({IMAGERY_URL}). Archival mosaic; shadows are not for your selected date.")
    else:
        st.caption("Lunar imagery is unavailable. The coordinate grid and site selection remain usable.")


def panorama(lookup: planner.Lookup, site: str, tl: pd.DataFrame, frame: int = 0) -> go.Figure:
    """Terrain skyline all around the site with the Sun's and Earth's paths over the mission."""
    sk = query("skyline", site)
    floor = min(sk["terrain_el_deg"].min(), tl["sun_el"].min(), tl["earth_el"].min()) - 1.0
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sk["azimuth_deg"], y=[floor] * len(sk), mode="lines",
                             line=dict(width=0), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=sk["azimuth_deg"], y=sk["terrain_el_deg"], mode="lines", fill="tonexty",
                             line=dict(color="#7c8791", width=1.5), fillcolor=GROUND, name="Terrain skyline",
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
        if frame:
            fig.add_trace(go.Scatter(x=[tl[f"{body}_az"].iloc[frame]], y=[tl[f"{body}_el"].iloc[frame]],
                                     mode="markers", marker=dict(color=colour, size=14, symbol="diamond"),
                                     name=f"{label} at selected hour", hoverinfo="skip"))
    dark_layout(fig, 380)
    fig.update_xaxes(title="Direction (azimuth, clockwise from lunar north)", range=[0, 360],
                     tickvals=[0, 90, 180, 270, 360], ticktext=["N 0°", "E 90°", "S 180°", "W 270°", "N 360°"],
                     gridcolor=RULE)
    fig.update_yaxes(title="Elevation (degrees)", gridcolor=RULE, zerolinecolor="#55616d")
    return fig


@st.fragment
def horizon_explorer(site: str, window: int, landing: dt.datetime) -> None:
    """Scrubbing reruns only this view, not ranking, imagery or date calendars."""
    tl = query("timeline", site, landing, window)
    st.header("Read the horizon.")
    st.caption(f"{site} · {window}-day mission · {ESTIMATE_NOTE}")
    chart = st.radio("Horizon view", ["Sky panorama", "Visibility over time"], horizontal=True,
                     label_visibility="collapsed")
    frame = st.slider("Explore the mission (hours after landing)", 0, len(tl) - 1, 0,
                       key=f"hour_{site}_{landing.isoformat()}_{window}")
    current = tl.iloc[frame]
    st.markdown(f"**{current.time_utc:%d %b %Y · %H:%M} UTC** · "
                f"Sun {current.sun_el:+.2f}° ({'visible' if current.sun_up else 'hidden'}) · "
                f"Earth {current.earth_el:+.2f}° ({'visible' if current.earth_up else 'hidden'})")
    if chart == "Sky panorama":
        fig = panorama(get_lookup(), site, tl, frame)
        note = ("The shaded profile is the LOLA terrain skyline. Hourly dots show Sun and Earth centres; "
                "faint dots are hidden. Rings mark landing; diamonds mark your selected hour. "
                "Visibility uses calibrated terrain limits, which can differ from the raw profile.")
    else:
        fig = margin_chart(tl)
        fig.add_vline(x=current.time_utc, line=dict(color=PICK, width=2))
        note = "Above zero, the top edge of the body clears its calibrated terrain limit; below zero it is hidden."
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, theme=None)
    st.caption(note)
    st.caption("Earth visible means any part of its disc; it does not guarantee a link to a specific ground station. "
               "Sun and Earth positions checked against NASA JPL Horizons: within 0.01°. "
               "Eclipse hours are reported separately and are not subtracted from sunlight ratios.")


def margin_chart(tl: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for body, colour, label in (("sun", SUN, "Sun"), ("earth", EARTH, "Earth")):
        fig.add_trace(go.Scatter(x=tl["time_utc"], y=tl[f"{body}_margin"], mode="lines",
                                 line=dict(color=colour, width=2), name=label,
                                 hovertemplate=label + " %{x|%d %b %H:%M} UTC<br>%{y:.2f}° above skyline<extra></extra>"))
    fig.add_hline(y=0, line=dict(color="#7c8791", width=1, dash="dash"))
    ecl = tl[tl["eclipse"] > 0]
    if len(ecl):
        fig.add_vrect(x0=ecl["time_utc"].iloc[0], x1=ecl["time_utc"].iloc[-1], fillcolor="#e63946",
                      opacity=0.25, line_width=0, annotation_text="eclipse", annotation_position="top left")
    dark_layout(fig, 300)
    fig.update_xaxes(title="Time (UTC)", gridcolor=RULE)
    fig.update_yaxes(title="Degrees above the terrain skyline", gridcolor=RULE)
    return fig


def date_heatmap(scan: pd.DataFrame, order: list[str], landing_day: dt.date, column: str, title: str) -> go.Figure:
    grid = scan.pivot(index="site", columns="date", values=column).loc[order]
    fig = go.Figure(go.Heatmap(
        z=grid.values, x=[pd.Timestamp(d) for d in grid.columns], y=grid.index, zmin=0, zmax=1,
        colorscale=[[0, "#11161b"], [0.5, "#2f4a57"], [0.95, "#8fc7bd"], [1, "#f6efcf"]],
        colorbar=dict(title="share", tickformat=".0%"),
        hovertemplate="%{y}<br>Landing %{x|%d %b %Y}<br>" + title + ": %{z:.0%}<extra></extra>"))
    if grid.columns[0] <= landing_day <= grid.columns[-1]:
        fig.add_vline(x=pd.Timestamp(landing_day), line=dict(color=PICK, width=2))
    dark_layout(fig, 430)
    fig.update_layout(title=dict(text=title, font=dict(color=INK, size=15)), margin=dict(l=10, r=10, t=45, b=10))
    fig.update_yaxes(automargin=True, tickfont=dict(size=11, color=INK))
    fig.update_xaxes(tickformat="%b %Y", dtick="M2", tickfont=dict(size=11, color=INK), automargin=True)
    return fig


# ------------------------------------------------------------------ step 2


def limit_args(limits: dict) -> dict:
    """The subset of settings that the calendar functions accept."""
    return {k: v for k, v in limits.items() if k not in ("slip_days", "weights")}


def choose_from_map() -> None:
    """Use only the site identifier returned with a plotted data point."""
    points = st.session_state.get("site_map", {}).get("selection", {}).get("points", [])
    if points and points[0].get("customdata"):
        site = points[0]["customdata"][0]
        if site in list(overview_sites()["site"]):
            st.session_state.selected_site = site
            st.session_state.site_picker = site


def choose_from_list() -> None:
    st.session_state.selected_site = st.session_state.site_picker


def site_panel(lookup: planner.Lookup, ranked: pd.DataFrame, limits: dict) -> None:
    names = list(ranked["site"])
    if st.session_state.selected_site not in names:
        st.session_state.selected_site = names[0]
    if st.session_state.get("site_picker") != st.session_state.selected_site:
        st.session_state.site_picker = st.session_state.selected_site
    site = st.selectbox("Selected landing site", names, key="site_picker", on_change=choose_from_list)
    st.session_state.selected_site = site
    row = next(r for r in ranked.itertuples() if r.site == site)
    window = st.session_state.window_days

    st.subheader(f"#{row.rank}  {row.site}")
    st.link_button("Stand at this site in 3D ↗", sim_link(row.site, st.session_state.landing_date, window))
    st.caption(f"{abs(row.lat):.3f}°S, {abs(row.lon):.3f}°{'E' if row.lon >= 0 else 'W'} · "
               f"surface height {row.height_m:,.0f} m")
    slip = limits["slip_days"]
    if row.passes:
        st.markdown(f'<div class="verdict">Meets all five limits · provisional score {row.score:.2f}</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div class="verdict no">Not recommended on this date</div>', unsafe_allow_html=True)
        st.caption("Why: " + row.fail_reasons + ".")

    def short(hours, up_now, what):
        return fmt_hours(hours, up_now, what).replace(" d ", "d ").replace(" h", "h").replace(f"{what} hidden at landing", "hidden")

    st.markdown(
        gauge("Sunlight in mission", SUN, row.sun_window, row.sun_window_worst, slip, limits["min_sun_window"])
        + gauge("Earth contact in mission", EARTH, row.earth_window, row.earth_window_worst, slip, limits["min_earth_window"])
        + '<div class="stats">'
        + f'<div><small>Mean slope</small><span>{row.slope_mean_deg:.1f}°</span></div>'
        + f'<div><small>Sunset in</small><span>{short(row.hours_to_sunset, row.sun_up_at_landing, "Sun")}</span></div>'
        + f'<div><small>Earthset in</small><span>{short(row.hours_to_earthset, row.earth_up_at_landing, "Earth")}</span></div>'
        + f'<div><small>Sun height</small><span>{row.sun_el_at_landing:+.1f}°</span></div></div>',
        unsafe_allow_html=True)
    gl = ground_link(row.site, landing_dt(), window)
    st.markdown("**Earth side: ground stations and weather**")
    g1, g2, g3 = st.columns(3)
    g1.metric("X-band", f"{gl['x_band']:.0%}", help="Share of the hours Earth is in view from the site in which at "
              "least one NASA Deep Space Network complex sees the Moon above 10°. X band (8.4 GHz) is barely affected by rain.")
    g2.metric("Ka, weather", f"{gl['ka_weather']:.0%}", help="Same, weighted by the chance it is dry at a "
              "complex in view (monthly precipitation days, climate normals). Ka band (32 GHz) loses margin in rain.")
    g3.metric("High-rate, all hours", f"{gl['end_to_end']:.0%}", help="Earth in view from the site AND a dry DSN "
              "complex in view, as a share of all mission hours.")
    st.markdown("".join(gauge(f"DSN {n} sees the Moon", EARTH, v, v, 0, 0) for n, v in gl["per_station"].items()),
                unsafe_allow_html=True)
    st.caption("The Moon has no weather; rain at the antennas on Earth weakens high-rate Ka-band links. Climatology, not a "
               "forecast: a wet day is counted as lost Ka for all its hours (conservative). Space weather (solar flares, "
               "particle storms) can also disrupt links and is not modelled. Not part of the ranking score.")
    if row.eclipse_hours > 0:
        st.warning(f"Lunar eclipse: {row.eclipse_hours:.0f} h. Not subtracted from the sunlight ratio.")
    st.caption("Share of the mission with any part of the disc above the terrain skyline. Thin line: your limit. "
               "Slope is the mean within 120 m. " + ESTIMATE_NOTE)
    if slip:
        st.markdown(f"**If the landing slips by up to {slip} days:** sunlight could fall to "
                    f"**{row.sun_window_worst:.0%}** and Earth contact to **{row.earth_window_worst:.0%}**. "
                    + ("Still meets the mission limits." if row.stable else "Would no longer meet the mission limits."))
    with st.expander("Resilience, terrain & long-term record"):
        c1, c2, c3 = st.columns(3)
        c1.metric("Longest dark", f"{row.longest_dark_h:.0f}h")
        c2.metric("Longest blackout", f"{row.longest_blackout_h:.0f}h")
        c3.metric("Steepest slope", f"{row.slope_max_deg:.1f}°", help="Within 120 m of the site.")
        st.caption(f"Slope at the site: {row.slope_site_deg:.1f}°. Long-term averages (NASA LOLA, 18.6 years): "
                   f"sunlight {row.sun_long_term:.0%}, Earth visibility {row.earth_long_term:.0%}.")
        st.write(f"Earth elevation at landing: **{row.earth_el_at_landing:+.2f}°**. "
                 f"Sun / Earth terrain margins: **{row.sun_margin_at_landing:+.2f}° / "
                 f"{row.earth_margin_at_landing:+.2f}°**.")

    near = query("nearest_passing_dates", landing_dt(), window, **limit_args(limits))
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
    left.markdown('<p class="eyebrow">02 / Site selection</p>', unsafe_allow_html=True)
    left.header("Find your foothold.")
    left.caption(f"Landing {landing_dt():%d %b %Y, %H:%M} UTC · {window} days on the surface")
    if right.button("Change date"):
        st.session_state.step = 1
        st.rerun()

    with st.sidebar:
        st.subheader("Mission criteria")
        st.caption("Set your limits, then apply them together.")
    with st.sidebar.form("criteria"):
        st.markdown("**Visibility & terrain**")
        limits = dict(
            min_sun_window=st.slider("Minimum sunlight in mission", 0, 100, 95, 5, format="%d%%", key="criterion_sun") / 100,
            min_earth_window=st.slider("Minimum Earth contact in mission", 0, 100, 95, 5, format="%d%%", key="criterion_earth") / 100,
            max_slope_deg=float(st.slider("Maximum mean slope", 1, 20, 10, format="%d°", key="criterion_slope")),
            min_sun_long_term=st.slider("Minimum long-term sunlight", 0, 85, 50, 5, format="%d%%", key="criterion_long_sun") / 100,
            min_earth_long_term=st.slider("Minimum long-term Earth visibility", 0, 100, 50, 5, format="%d%%", key="criterion_long_earth") / 100,
            slip_days=st.slider("Possible landing slip (days either way)", 0, 30, 14, key="criterion_slip"),
        )
        st.markdown("**Score weights**")
        limits["weights"] = {
            "sunlight": st.slider("Sunlight", 0.0, 3.0, 1.0, 0.5, key="criterion_weight_sun"),
            "earth": st.slider("Earth contact", 0.0, 3.0, 1.0, 0.5, key="criterion_weight_earth"),
            "flatness": st.slider("Flatness", 0.0, 3.0, 1.0, 0.5, key="criterion_weight_flatness"),
        }
        if sum(limits["weights"].values()) == 0:
            st.warning("All weights are zero; using equal weights.")
            limits["weights"] = None
        st.form_submit_button("Apply criteria", type="primary", width="stretch")

    ranked = query("rank_for_date", landing_dt(), window, **limits)
    if st.session_state.selected_site not in list(ranked.site):
        st.session_state.selected_site = ranked.site.iloc[0]
    passing = int(ranked["passes"].sum())
    if passing:
        st.markdown(f'<div class="result-line"><strong>{passing} / {len(ranked)} sites meet your limits</strong>'
                    ' · Select a numbered location to inspect it.</div>', unsafe_allow_html=True)
    else:
        others_ok = ranked[(ranked.sun_window >= limits["min_sun_window"]) & (ranked.slope_mean_deg <= limits["max_slope_deg"])]
        step = int(others_ok.earth_window.max() * 100 // 5 * 5) if len(others_ok) else 0
        if window >= 21:
            st.info("For missions longer than about three weeks, no south-pole site keeps Earth in view 95% of the time: "
                    "Earth's wobble in the lunar sky (libration, about 27 days) takes it below the horizon for part of every cycle.")
        if 50 <= step < round(limits["min_earth_window"] * 100):
            st.button(f"Accept Earth contact ≥ {step}%", on_click=lambda v=step: st.session_state.update(criterion_earth=v))
        near = query("nearest_passing_dates", landing_dt(), window, **limit_args(limits))
        near = near.dropna(subset=["days_to_nearest"]).sort_values("days_to_nearest")
        if len(near):
            best = near.iloc[0]
            dates = [d for d in (best["previous_date"], best["next_date"]) if d is not None and not pd.isna(d)]
            closest = min(dates, key=lambda d: abs((d - landing_dt().date()).days))
            st.error(f"No site passes every limit on this date. The nearest option is **{best['site']}** "
                     f"with a landing on **{closest:%d %b %Y}** ({int(best['days_to_nearest'])} days away).")
        else:
            st.error("No site passes these limits on any date in 2027-2030. Loosen a limit in the sidebar.")

    lk = get_lookup()
    n_sites, n_hours = lk.sun_el.shape
    st.markdown(
        '<div class="stats datascale">'
        f'<div><small>Candidate sites</small><span>{n_sites}</span></div>'
        f'<div><small>Hourly time steps</small><span>{n_hours:,}</span></div>'
        f'<div><small>Site-hours of Sun &amp; Earth geometry</small><span>{n_sites * n_hours:,}</span></div>'
        f'<div><small>DSN station-hours</small><span>{3 * n_hours:,}</span></div>'
        f'<div><small>Landing dates × lengths you can test</small><span>{(LAST_DAY - FIRST_DAY).days + 1:,} × 60</span></div>'
        '</div>', unsafe_allow_html=True)
    st.caption(f"Every result on this page is read from {n_sites * n_hours * 4:,} precomputed angles "
               "(Sun and Earth elevation and azimuth per site and hour, 2027-2031), checked against NASA JPL Horizons, "
               "with terrain skylines from NASA LOLA elevation models.")
    weights = limits["weights"] or dict(sunlight=1, earth=1, flatness=1)
    st.caption(f"Score weights · Sunlight {weights['sunlight']:g} · Earth contact {weights['earth']:g} · "
               f"Flatness {weights['flatness']:g}. Provisional weighted score. Edit in the criteria sidebar (top left).")
    view = st.radio("Workspace", ["Sites", "Compare dates", "Custom coordinates"], horizontal=True,
                    label_visibility="collapsed", key="workspace")

    if view == "Sites":
        map_col, info_col = st.columns([5, 4])
        with info_col:
            site_panel(lookup, ranked, limits)
        with map_col:
            st.markdown('<div class="atlas-heading"><span>SOUTH POLAR STEREOGRAPHIC</span><span>84°S–90°S</span></div>',
                        unsafe_allow_html=True)
            st.plotly_chart(polar_map(ranked, st.session_state.selected_site), width="stretch",
                            config={"displayModeBar": True, "displaylogo": False, "scrollZoom": False,
                                    "modeBarButtonsToRemove": ["select2d", "lasso2d", "toImage", "autoScale2d"]}, theme=None,
                            key="site_map", on_select=choose_from_map, selection_mode="points")
            st.markdown(f'<div class="legend"><span><b style="color:{PASS}">●</b>Meets limits</span>'
                        f'<span><b style="color:{FAIL}">●</b>Below a limit</span>'
                        f'<span><b style="color:{PICK}">◉</b>Selected</span></div>', unsafe_allow_html=True)
            st.caption("Click a site · Zoom with the buttons on the map · Drag to pan · Double-click to reset. Numbers are ranks; "
                       "labels connect to the true NASA LOLA positions.")
            image_credit()

        site = st.session_state.selected_site
        horizon_explorer(site, window, landing_dt())

        st.subheader("All candidate sites")
        full = ranked.copy()
        links = [ground_link(n, landing_dt(), window) for n in full.site]
        full["ka_weather"] = [g["ka_weather"] for g in links]
        full["high_rate"] = [g["end_to_end"] for g in links]
        table = full[["rank", "site", "score", "sun_window", "earth_window", "high_rate", "slope_mean_deg", "slope_max_deg",
                      "sun_window_worst", "earth_window_worst", "longest_dark_h", "longest_blackout_h", "eclipse_hours",
                      "max_sun_el_window", "sun_long_term", "earth_long_term", "passes", "fail_reasons"]].rename(columns={
            "rank": "Rank", "site": "Site", "score": "Score", "sun_window": "Sunlight",
            "earth_window": "Earth contact", "high_rate": "High-rate link (weather)", "slope_mean_deg": "Slope (°)",
            "slope_max_deg": "Steepest (°)", "sun_window_worst": "Sunlight if slipped", "earth_window_worst": "Contact if slipped",
            "longest_dark_h": "Longest dark (h)", "longest_blackout_h": "Longest blackout (h)", "eclipse_hours": "Eclipse (h)",
            "max_sun_el_window": "Max Sun height (°)", "sun_long_term": "Sun, 18.6-yr", "earth_long_term": "Earth, 18.6-yr",
            "passes": "Passes", "fail_reasons": "Why not"})
        st.caption(f"{len(table)} sites × {len(table.columns)} measures for a landing on {landing_dt():%d %b %Y %H:%M} UTC, "
                   f"{window} days. Scroll sideways for all columns.")
        bar = dict(format="percent", min_value=0, max_value=1)
        st.dataframe(table, hide_index=True, width="stretch", column_config={
            "Score": st.column_config.NumberColumn(format="%.2f"),
            "Sunlight": st.column_config.ProgressColumn(**bar),
            "Earth contact": st.column_config.ProgressColumn(**bar),
            "Sunlight if slipped": st.column_config.ProgressColumn(**bar),
            "Contact if slipped": st.column_config.ProgressColumn(**bar),
            "Slope (°)": st.column_config.NumberColumn(format="%.1f"),
            "Steepest (°)": st.column_config.NumberColumn(format="%.1f"),
            "High-rate link (weather)": st.column_config.ProgressColumn(**bar),
            "Sun, 18.6-yr": st.column_config.ProgressColumn(**bar),
            "Earth, 18.6-yr": st.column_config.ProgressColumn(**bar),
            "Max Sun height (°)": st.column_config.NumberColumn(format="%.1f"),
        })
        st.download_button("Download all measures (CSV)", full.drop(columns=["x_km", "y_km"], errors="ignore").to_csv(index=False),
                           file_name=f"lunar_sites_{landing_dt():%Y%m%d}_{window}d.csv", mime="text/csv")

    elif view == "Compare dates":
        st.header("A different date. A different outlook.")
        st.write("How each site would do for the same mission length on every landing date. "
                 "The orange line is the chosen date; brighter is better.")
        years = [2027, 2028, 2029, 2030]
        year = st.radio("Year", years, horizontal=True, index=years.index(landing_dt().year))
        scan = query("date_scan", window, hour_utc=landing_dt().hour)
        scan = scan[[d.year == year for d in scan["date"]]].copy()
        scan["both"] = scan[["sun_window", "earth_window"]].min(axis=1)
        order = list(ranked["site"])[::-1]
        metric = st.selectbox("Map layer", ["Lower of sunlight and Earth contact", "Sunlight in mission", "Earth contact in mission"])
        column = {"Lower of sunlight and Earth contact": "both", "Sunlight in mission": "sun_window",
                  "Earth contact in mission": "earth_window"}[metric]
        st.plotly_chart(date_heatmap(scan, order, landing_dt().date(), column, metric),
                        width="stretch", theme=None)
        st.caption("Visibility only, not a pass/fail map. Sunlight ratios do not subtract lunar eclipse hours; "
                   "inspect a mission in Sites for its eclipse duration. " + ESTIMATE_NOTE)
        best = query("best_dates", st.session_state.selected_site, window)
        st.write(f"**Best landing dates for {st.session_state.selected_site}, 2027-2030:** "
                 + ", ".join(f"{d:%d %b %Y}" for d in best["date"]) + ".")
        st.caption("Best dates use the planner's 00:00 UTC reference, based on Sun and Earth visibility. "
                   "They do not apply your slope or pass/fail limits. The heat map uses your selected UTC hour.")

    else:
        st.header("Explore another coordinate.")
        st.write("Check any point on the Moon for the same landing date and mission length.")
        with st.form("custom_point"):
            c1, c2 = st.columns(2)
            lat = c1.number_input("Latitude (degrees, south is negative)", -90.0, 90.0, -89.5, 0.1, format="%.3f", key="custom_lat")
            lon = c2.number_input("East longitude (degrees, west is negative)", -180.0, 360.0, 0.0, 0.5, format="%.3f", key="custom_lon")
            st.form_submit_button("Evaluate coordinates", type="primary")
        summary, ctl = custom_conditions(lat, lon, landing_dt(), window)
        st.warning("Flat-horizon estimate, terrain not included. Real terrain hides the Sun and Earth more "
                   "often, so these figures are optimistic. Terrain and slope: not available yet. "
                   "Eclipse hours: not available yet for custom coordinates; sunlight ratios do not subtract eclipses.")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Sunlight in mission", f"{summary['sun_window']:.0%}")
        m2.metric("Earth contact in mission", f"{summary['earth_window']:.0%}")
        m3.metric("Time to sunset", fmt_hours(summary["hours_to_sunset"], bool(ctl["sun_up"].iloc[0]), "Sun"))
        m4.metric("Time to Earthset", fmt_hours(summary["hours_to_earthset"], bool(ctl["earth_up"].iloc[0]), "Earth"))
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=ctl["time_utc"], y=ctl["sun_el"], line=dict(color=SUN, width=2), name="Sun"))
        fig.add_trace(go.Scatter(x=ctl["time_utc"], y=ctl["earth_el"], line=dict(color=EARTH, width=2), name="Earth"))
        fig.add_hline(y=0, line=dict(color="#7c8791", width=1, dash="dash"))
        dark_layout(fig, 320)
        fig.update_xaxes(title="Time (UTC)", gridcolor=RULE)
        fig.update_yaxes(title="Elevation above a level horizon (degrees)", gridcolor=RULE)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, theme=None)

    st.caption("Data: NASA LRO LOLA visibility maps and elevation models (PDS Geosciences Node), Artemis III "
               "candidate regions (Moon Trek). Sun and Earth positions checked against NASA JPL Horizons. "
               "Built by Team_of_AEers with help from Claude (Anthropic) and OpenAI Codex; no AI-generated imagery.")


init_state()
styles()
masthead()
if st.session_state.step == 1:
    page_date()
else:
    page_sites()
