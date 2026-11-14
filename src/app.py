"""Lunar Landing Optimal System - planning tool interface.

AI-assisted: written by Claude (Anthropic), 2026-11-14.

REFERENCE INTERFACE ONLY. The final visual design is being made separately;
this file shows the agreed flow working end to end and how to call the logic
in sites.py. It can be replaced without touching the logic.

Flow: step 1 pick a planned landing date, step 2 choose a landing site on a
map of the lunar south pole.

Run with:  streamlit run src/app.py

What is real and what is not yet:
- Long-term Sun and Earth visibility per site are real NASA LOLA figures.
- Conditions for the chosen date (Sun/Earth position, time to sunset) are NOT
  computed yet. The app says so instead of showing made-up numbers.
"""

from __future__ import annotations

import datetime as dt
import math

import plotly.graph_objects as go
import streamlit as st

from sites import MOON_RADIUS_M, load_sites, rank_sites

st.set_page_config(page_title="Lunar Landing Optimal System", layout="wide")

PASS_COLOUR = "#2a9d8f"
FAIL_COLOUR = "#8d99ae"
SELECT_COLOUR = "#e76f51"


@st.cache_data
def get_sites():
    return load_sites()


def init_state() -> None:
    st.session_state.setdefault("step", 1)
    st.session_state.setdefault("landing_date", dt.date(2028, 1, 1))
    st.session_state.setdefault("landing_time", dt.time(0, 0))
    st.session_state.setdefault("window_days", 14)
    st.session_state.setdefault("selected_site", None)


def landing_datetime() -> dt.datetime:
    return dt.datetime.combine(st.session_state.landing_date, st.session_state.landing_time)


# ---------------------------------------------------------------- step 1


def page_date() -> None:
    st.title("Lunar Landing Optimal System")
    st.caption("A planning tool for choosing when and where to land at the lunar south pole.")

    left, _ = st.columns([2, 1])
    with left:
        st.header("Step 1 of 2: When do you plan to land?")
        c1, c2 = st.columns(2)
        st.session_state.landing_date = c1.date_input(
            "Planned landing date (UTC)",
            value=st.session_state.landing_date,
            min_value=dt.date(2026, 1, 1),
            max_value=dt.date(2040, 12, 31),
        )
        st.session_state.landing_time = c2.time_input(
            "Landing time (UTC)", value=st.session_state.landing_time
        )
        st.session_state.window_days = st.slider(
            "Mission length on the surface (days)",
            min_value=1,
            max_value=60,
            value=st.session_state.window_days,
            help="Sunlight and Earth contact will be assessed over this period after landing.",
        )
        st.write(
            f"Landing **{landing_datetime():%d %b %Y, %H:%M} UTC**, "
            f"operating for **{st.session_state.window_days} days**."
        )
        if st.button("Find landing sites", type="primary"):
            st.session_state.step = 2
            st.rerun()

    with st.expander("Why does the date matter so much?"):
        st.write(
            "At the Moon's south pole the Sun and the Earth both stay close to the horizon. "
            "A ridge a few kilometres away can hide either of them for days. Whether a site "
            "has power (Sun) and a radio link (Earth) therefore depends strongly on the date."
        )


# ---------------------------------------------------------------- step 2


def polar_map(ranked, selected: str | None) -> go.Figure:
    fig = go.Figure()

    # Latitude circles and longitude spokes.
    max_r_km = 2 * MOON_RADIUS_M * math.tan(math.radians(5.0) / 2) / 1000.0  # 85 deg S
    for lat in (-89, -88, -87, -86, -85):
        r = 2 * MOON_RADIUS_M * math.tan(math.radians(90 + lat) / 2) / 1000.0
        angles = [math.radians(a) for a in range(0, 361, 3)]
        fig.add_trace(
            go.Scatter(
                x=[r * math.sin(a) for a in angles],
                y=[r * math.cos(a) for a in angles],
                mode="lines",
                line=dict(color="#3a4a5e", width=1),
                hoverinfo="skip",
                showlegend=False,
            )
        )
        fig.add_annotation(x=0, y=-r, text=f"{-lat}°S", showarrow=False, font=dict(color="#7b8794", size=10), yshift=-8)
    for lon in range(0, 360, 30):
        a = math.radians(lon)
        fig.add_trace(
            go.Scatter(
                x=[0, max_r_km * math.sin(a)],
                y=[0, max_r_km * math.cos(a)],
                mode="lines",
                line=dict(color="#3a4a5e", width=1),
                hoverinfo="skip",
                showlegend=False,
            )
        )
    fig.add_annotation(x=0, y=max_r_km, text="0° (towards Earth)", showarrow=False, font=dict(color="#cbd5e1", size=11), yshift=12)
    fig.add_annotation(x=max_r_km, y=0, text="90°E", showarrow=False, font=dict(color="#cbd5e1", size=11), xshift=22)
    fig.add_annotation(x=-max_r_km, y=0, text="90°W", showarrow=False, font=dict(color="#cbd5e1", size=11), xshift=-22)
    fig.add_annotation(x=0, y=-max_r_km, text="180°", showarrow=False, font=dict(color="#cbd5e1", size=11), yshift=-22)

    colours = [
        SELECT_COLOUR if row.site == selected else (PASS_COLOUR if row.passes else FAIL_COLOUR)
        for row in ranked.itertuples()
    ]
    fig.add_trace(
        go.Scatter(
            x=ranked["x_km"],
            y=ranked["y_km"],
            mode="markers+text",
            text=[str(r) for r in ranked["rank"]],
            textfont=dict(color="white", size=11),
            marker=dict(size=24, color=colours, line=dict(color="white", width=1)),
            customdata=ranked[["site", "sun_long_term", "earth_long_term", "lat", "lon"]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Sunlight (long-term): %{customdata[1]:.0%}<br>"
                "Earth in view (long-term): %{customdata[2]:.0%}<br>"
                "%{customdata[3]:.3f}°, %{customdata[4]:.3f}°<extra></extra>"
            ),
            showlegend=False,
        )
    )
    pad = max_r_km * 1.15
    fig.update_layout(
        height=620,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="#0f1722",
        plot_bgcolor="#0f1722",
        xaxis=dict(visible=False, range=[-pad, pad]),
        yaxis=dict(visible=False, range=[-pad, pad], scaleanchor="x", scaleratio=1),
        dragmode="pan",
    )
    return fig


def site_card(row) -> None:
    st.subheader(f"#{row.rank}  {row.site}")
    st.caption(f"{abs(row.lat):.3f}°S, {abs(row.lon):.3f}°{'E' if row.lon >= 0 else 'W'}")

    c1, c2 = st.columns(2)
    c1.metric("Sunlight, long-term", f"{row.sun_long_term:.0%}", help="Share of time the Sun is visible, averaged over 18.6 years.")
    c2.metric("Earth in view, long-term", f"{row.earth_long_term:.0%}", help="Share of time Earth is visible, averaged over 18.6 years.")
    st.progress(row.sun_long_term, text="Power potential")
    st.progress(row.earth_long_term, text="Direct-to-Earth communication")

    if row.passes:
        st.success("Passes the long-term limits.")
    else:
        st.warning("Fails a long-term limit and is not recommended.")

    st.markdown(f"**Conditions for {landing_datetime():%d %b %Y}**")
    st.info(
        "Not available yet. Sun and Earth position at this site on the chosen date, "
        "time until sunset and Earthset, and the mission-window sunlight and contact "
        "ratios will appear here once the date calculations are connected."
    )


def page_sites() -> None:
    top_left, top_right = st.columns([4, 1])
    top_left.header("Step 2 of 2: Choose a landing site")
    top_left.caption(
        f"Landing {landing_datetime():%d %b %Y, %H:%M} UTC · {st.session_state.window_days} days on the surface"
    )
    if top_right.button("Change date"):
        st.session_state.step = 1
        st.rerun()

    with st.sidebar:
        st.subheader("Limits")
        min_sun = st.slider("Minimum long-term sunlight", 0, 90, 50, step=5, format="%d%%") / 100
        min_earth = st.slider("Minimum long-term Earth visibility", 0, 100, 50, step=5, format="%d%%") / 100
        st.caption("No location at the south pole exceeds 88% long-term sunlight (NASA LOLA data).")

    ranked = rank_sites(get_sites(), min_sun, min_earth)
    names = list(ranked["site"])
    if st.session_state.selected_site not in names:
        st.session_state.selected_site = names[0]

    passing = int(ranked["passes"].sum())
    st.write(f"**{passing} of {len(ranked)}** candidate sites pass the limits.")

    map_col, info_col = st.columns([3, 2])
    with map_col:
        st.plotly_chart(
            polar_map(ranked, st.session_state.selected_site),
            width="stretch",
            config={"displayModeBar": False, "scrollZoom": True},
        )
        st.caption(
            "Lunar south pole, 85°S to the pole. Numbers are ranks; grey sites fail a limit. "
            "Ranking currently uses long-term averages only, not the chosen date."
        )
    with info_col:
        st.session_state.selected_site = st.selectbox(
            "Site", names, index=names.index(st.session_state.selected_site)
        )
        row = next(r for r in ranked.itertuples() if r.site == st.session_state.selected_site)
        site_card(row)

    st.subheader("All candidate sites")
    table = ranked[["rank", "site", "sun_long_term", "earth_long_term", "passes"]].rename(
        columns={
            "rank": "Rank",
            "site": "Site",
            "sun_long_term": "Sunlight (long-term)",
            "earth_long_term": "Earth in view (long-term)",
            "passes": "Passes limits",
        }
    )
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        column_config={
            "Sunlight (long-term)": st.column_config.ProgressColumn(format="percent", min_value=0, max_value=1),
            "Earth in view (long-term)": st.column_config.ProgressColumn(format="percent", min_value=0, max_value=1),
        },
    )
    st.caption(
        "Data: NASA LRO LOLA average visibility maps (60 m/px) and Moon Trek Artemis III regions. "
        "Each region is shown at its best combined spot."
    )


init_state()
if st.session_state.step == 1:
    page_date()
else:
    page_sites()
