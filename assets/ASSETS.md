# Web assets for Lunar Landing Optimal System

Lightweight, openly licensed assets for the team's Streamlit app. Total size of
all icons: **2,935 bytes (~2.9 KB)** — small enough that they add no noticeable
load time.

## Icons

Source: [Lucide](https://lucide.dev/) — open-source icon set, **ISC license**
(free for any use, including commercial; keep the license notice if you
redistribute the files themselves). Each file is a single 24×24 line icon that
inherits the current text colour (`stroke="currentColor"`), so it recolors
automatically with the app's dark theme. Files live in `icons/`.

| File | Icon | Use in the app | Source |
| --- | --- | --- | --- |
| `icons/rocket.svg` | rocket | Mission / launch, hero | https://lucide.dev/icons/rocket |
| `icons/sun.svg` | sun | Sunlight / solar power | https://lucide.dev/icons/sun |
| `icons/earth.svg` | earth | Earth visibility / comms | https://lucide.dev/icons/earth |
| `icons/moon.svg` | moon | Lunar site / Moon | https://lucide.dev/icons/moon |
| `icons/map-pin.svg` | map pin | Landing site marker | https://lucide.dev/icons/map-pin |
| `icons/signal.svg` | signal | Direct-to-Earth link | https://lucide.dev/icons/signal |
| `icons/satellite-dish.svg` | satellite dish | Comms / ground link | https://lucide.dev/icons/satellite-dish |

Raw files (same set, MIT/ISC):
`https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/<name>.svg`

## Fonts — keep what the app already uses

The app already uses **Space Grotesk** (headings) + **IBM Plex Mono**
(numbers/labels). Do **not** add another font — a new font family costs a
fresh download and slows the first paint. Both are on Google Fonts under the
**SIL Open Font License** and the team already loads them.

Fast-loading setup (put in `.streamlit/config.toml` or the page `<head>` via
`st.markdown(..., unsafe_allow_html=True)`):

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
```

Notes:
- `display=swap` — text renders immediately in a fallback font, then swaps
  when the webfont arrives (no invisible-text delay).
- Only the weights actually used (500/700, 400/600) — every extra weight is
  another download.
- `preconnect` to both Google Fonts hosts removes one round-trip each.

## CSS snippet — paste into the Streamlit app

Copy the `icons/` folder into the repo (e.g. `assets/icons/`) and paste this
into `src/app.py` once, near the top:

```python
import pathlib

ICONS = pathlib.Path(__file__).parent.parent / "assets" / "icons"

def icon(name: str, size: int = 20) -> str:
    """Inline an SVG icon so it inherits the surrounding text colour."""
    svg = (ICONS / f"{name}.svg").read_text()
    return svg.replace('width="24"', f'width="{size}"').replace(
        'height="24"', f'height="{size}"'
    )

st.markdown("""
<style>
/* Fade-in for panels and cards */
@keyframes fade-in { from { opacity: 0; } to { opacity: 1; } }
.fade-in { animation: fade-in 0.5s ease-out both; }

/* Slow Sun glow pulse (opacity only — cheap on the GPU) */
@keyframes sun-pulse { 0%, 100% { opacity: 0.55; } 50% { opacity: 1; } }
.sun-glow { animation: sun-pulse 4s ease-in-out infinite; }

/* Respect users who prefer no motion */
@media (prefers-reduced-motion: reduce) {
  .fade-in, .sun-glow { animation: none; }
}
</style>
""", unsafe_allow_html=True)
```

Use it like this:

```python
st.markdown(f'{icon("sun", 22)} Sunlight 88%', unsafe_allow_html=True)
st.markdown(f'<span class="sun-glow">{icon("sun", 28)}</span>', unsafe_allow_html=True)
```

## Animation rules (why it stays fast)

- Only `opacity` (and `transform`, if you add movement) is animated — these
  run on the GPU compositor and never trigger layout or repaint of the page.
- No JavaScript animation loops, no GIFs, no video backgrounds.
- One 4-second glow pulse instead of many fast ones; `prefers-reduced-motion`
  turns it off for users who ask for that.
- The two big images already in `assets/` (`launchpad.jpg`, `moon.jpg`) are
  the heaviest assets in the app — lazy-load them (only render when their tab
  is open) instead of loading both on first paint.

## Licenses

- Icons: Lucide, ISC license — https://github.com/lucide-icons/lucide/blob/main/LICENSE
- Fonts: Space Grotesk + IBM Plex Mono, SIL Open Font License —
  https://fonts.google.com/specimen/Space+Grotesk and
  https://fonts.google.com/specimen/IBM+Plex+Mono
