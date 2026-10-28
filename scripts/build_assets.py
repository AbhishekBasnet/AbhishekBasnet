#!/usr/bin/env python3
"""Build the artwork for the GitHub profile README.

Writes four SVGs into assets/:

    landscape-light.svg  landscape-dark.svg   header: sky, ridge, summits, name
    legend-light.svg     legend-dark.svg      key for the three summits

The README picks the light or dark file with <picture>. To change the art,
edit the constants below and run:

    python3 scripts/build_assets.py

Animation timeline (seconds after the image loads):

    0.0 – 3.2   intro, once      ridge draws, summits fade up, sun/moon rises
    3.2 – 4.8   sky, once        clouds or stars fade in
    5.0 →       loop, every 12s  labels glow → light runs along the ridge →
                                 ripple leaves the sun/moon → rest
    always      ambient          glow breathes, stars twinkle, clouds sway
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from string import Template
from textwrap import dedent, indent

ASSETS = Path(__file__).resolve().parent.parent / "assets"

# ── Canvas ───────────────────────────────────────────────────────────────────

VIEW_X, VIEW_Y, WIDTH, HEIGHT = 46, 36, 808, 370
LEFT, RIGHT = 48, 852

SANS = "'Helvetica Neue', Helvetica, 'Segoe UI', Arial, sans-serif"
MONO = "ui-monospace, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

# ── Palette (Nord) ───────────────────────────────────────────────────────────

THEMES = {
    "light": dict(ink="#2E3440", muted="#6B7891", accent="#5E81AC", rule="#D8DEE9",
                  orb="#BF616A", glow="#D08770", ripple="#BF616A"),
    "dark": dict(ink="#ECEFF4", muted="#8F9BB3", accent="#88C0D0", rule="#3B4252",
                 orb="#E5E9F0", glow="#E5E9F0", ripple="#D8DEE9"),
}
SNOW = "#ECEFF4"
CLOUD = "#E5E9F0"

# ── Text ─────────────────────────────────────────────────────────────────────

NAME = "Abhishek Man Basnet"
ROLE = "backend engineer · nepal"
COORDS = "28.39° N   84.12° E"  # geographic centre of Nepal
TITLE = f"{NAME}, backend engineer — flutter, go, fastapi"

# ── Landscape ────────────────────────────────────────────────────────────────

RIDGE = [
    (48, 332), (110, 322), (150, 326), (210, 292), (236, 300), (268, 264), (300, 284),
    (338, 272), (380, 296), (420, 254), (452, 220), (486, 246), (516, 238), (560, 284),
    (604, 272), (652, 250), (690, 282), (740, 306), (790, 298), (852, 320),
]
SUMMITS = [(268, 264, "flutter"), (452, 220, "go"), (652, 250, "fastapi")]
LABEL_Y = 170
GROUND_Y = 342
ORB = (792, 92)  # the sun by day, the moon by night


@dataclass(frozen=True)
class Cloud:
    x: float          # left edge at rest
    y: float          # flat base
    scale: float
    reach: float      # px it sways either side of rest
    period: float     # seconds for one crossing, left to right
    phase: float      # 0–1, where in the sway it starts, so clouds move out of step


@dataclass(frozen=True)
class Star:
    x: float
    y: float
    r: float
    opacity: float
    period: float     # seconds for one twinkle
    delay: float


SKY_CLOUDS = [
    Cloud(108, 126, 0.6, reach=18, period=44, phase=.3),
    Cloud(520, 78, 1.0, reach=24, period=55, phase=.7),
    Cloud(628, 132, 0.5, reach=16, period=38, phase=.1),
    Cloud(750, 108, 0.8, reach=5, period=30, phase=.5),   # stays over the sun's lower edge
]

STARS = [
    Star(118, 108, 1.4, .80, 3.6, 4.8), Star(186, 150, 1.1, .60, 4.4, 5.6),
    Star(236, 80, 1.5, .90, 3.1, 5.1), Star(338, 130, 1.0, .55, 5.0, 6.0),
    Star(372, 64, 1.8, 1.0, 4.2, 4.9), Star(520, 96, 1.2, .70, 3.4, 5.3),
    Star(566, 148, 1.0, .55, 4.8, 6.4), Star(612, 66, 1.4, .85, 3.8, 5.8),
    Star(712, 124, 1.1, .65, 4.6, 5.2), Star(848, 70, 1.4, .80, 3.3, 6.1),
    Star(836, 150, 1.0, .55, 5.2, 5.5),
]
BRIGHT_STAR = STARS[4]

# ── Timeline (seconds) ───────────────────────────────────────────────────────

LOOP = 12.0
LOOP_START = 5.0
LABEL_GLOW, LABEL_STAGGER = 1.4, 0.7   # step 2: each label, one after another
TRACE_AT, TRACE_LEN = 3.0, 2.4         # step 3: light along the ridge
RIPPLE_AT, RIPPLE_LEN = 5.2, 2.64      # step 4: ring leaving the sun/moon


# ── Helpers ──────────────────────────────────────────────────────────────────

def num(v: float) -> str:
    """Shortest clean form of a number: 12.0 → 12, 0.50 → .5"""
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s[1:] if s.startswith("0.") else s


def pct(seconds: float) -> str:
    return f"{num(seconds / LOOP * 100)}%"


def ridge_path() -> str:
    return "M" + " L".join(f"{x} {y}" for x, y in RIDGE)


def cloud(c: Cloud) -> str:
    k = c.scale
    # a negative delay starts the sway part-way through, so it is already moving on load
    timing = f"--reach: {num(c.reach)}px; --t: {num(c.period)}s; --d: -{num(c.phase * c.period)}s"
    parts = [
        f'<rect x="{num(c.x)}" y="{num(c.y - 10*k)}" width="{num(60*k)}" height="{num(10*k)}" rx="{num(5*k)}"/>',
        f'<circle cx="{num(c.x + 18*k)}" cy="{num(c.y - 10*k)}" r="{num(10*k)}"/>',
        f'<circle cx="{num(c.x + 34*k)}" cy="{num(c.y - 14*k)}" r="{num(13*k)}"/>',
        f'<circle cx="{num(c.x + 48*k)}" cy="{num(c.y - 9*k)}" r="{num(8*k)}"/>',
    ]
    inner = "\n      ".join(parts)
    return f'<g class="cloud" style="{timing}">\n      {inner}\n    </g>'


def star(s: Star) -> str:
    return (f'<circle class="star" cx="{s.x}" cy="{s.y}" r="{num(s.r)}" '
            f'style="--t: {num(s.period)}s; --d: {num(s.delay)}s; opacity: {num(s.opacity)}"/>')


def summit(i: int, x: int, y: int, label: str) -> str:
    return f"""  <g class="summit" style="--i: {i}">
    <line class="leader" x1="{x}" y1="{y - 8}" x2="{x}" y2="{LABEL_Y + 12}"/>
    <circle class="dot" cx="{x}" cy="{y}" r="2.5"/>
    <g class="pulse">
      <text class="label halo" filter="url(#blur)" x="{x}" y="{LABEL_Y}">{label}</text>
      <text class="label" x="{x}" y="{LABEL_Y}">{label}</text>
    </g>
  </g>"""


# ── Landscape SVG ────────────────────────────────────────────────────────────

STYLE = Template("""
    /* palette */
    svg { --ink: $ink; --muted: $muted; --accent: $accent; --rule: $rule;
          --orb: $orb; --glow: $glow; --ripple: $ripple;
          --sans: $sans;
          --mono: $mono; }

    /* type */
    .name  { font: 300 30px var(--sans); letter-spacing: -.3px; fill: var(--ink); }
    .meta  { font: 400 11px var(--mono); letter-spacing: 1.8px; fill: var(--muted); }
    .label { font: 500 12px var(--mono); letter-spacing: 2px; fill: var(--ink); text-anchor: middle; }

    /* shapes */
    .ridge  { fill: none; stroke: var(--accent); stroke-width: 1.25; stroke-linejoin: miter; }
    .ground { stroke: var(--rule); stroke-width: 1; }
    .leader { stroke: var(--muted); stroke-width: 1; stroke-dasharray: 2 3; }
    .dot    { fill: var(--accent); }
    .body   { fill: var(--orb); }
    .glow   { fill: var(--glow); }
    .cloud  { fill: $cloud; }
    .star, .haze { fill: $snow; }
    .haze   { opacity: .18; }

    /* 1 · intro, plays once */
    .ridge  { stroke-dasharray: 1; animation: draw 2.6s cubic-bezier(.6, .05, .3, 1) both; }
    .summit { animation: fade-up .8s ease-out calc(1.6s + var(--i) * .4s) backwards; }
    .orb    { animation: rise 3s ease-out backwards; }
    .sky    { animation: appear 1.6s ease-out 3.2s backwards; }

    /* 2 · labels glow in turn */
    .pulse       { transform-box: fill-box; transform-origin: center;
                   animation: label-scale ${loop}s ease-in-out calc(${loop_start}s + var(--i) * ${stagger}s) infinite; }
    .pulse .label { animation: label-tint ${loop}s ease-in-out infinite; animation-delay: inherit; }
    .pulse .halo  { fill: var(--accent); opacity: 0; animation-name: label-glow; }

    /* 3 · light runs along the ridge */
    .trace      { fill: none; stroke-linecap: round; stroke-dasharray: .08 1.2; stroke-dashoffset: .08; opacity: 0;
                  animation: trace ${loop}s ease-in-out ${trace_at}s infinite; }
    .trace.core { stroke: var(--ink); stroke-width: 2; }
    .trace.halo { stroke: var(--accent); stroke-width: 5; }

    /* 4 · ripple leaves the sun / moon */
    .ripple        { transform-box: fill-box; transform-origin: center;
                     animation: ripple-grow ${loop}s cubic-bezier(.2, .6, .3, 1) ${ripple_at}s infinite; }
    .ripple circle { fill: none; stroke: var(--ripple); stroke-width: 1.6; vector-effect: non-scaling-stroke; opacity: 0;
                     animation: ripple-fade ${loop}s linear ${ripple_at}s infinite; }

    /* ambient, always running */
    .glow       { opacity: .1; transform-box: fill-box; transform-origin: center;
                  animation: breathe 9s ease-in-out 3s infinite alternate; }
    .star       { animation: twinkle var(--t) ease-in-out var(--d) infinite; }
    .cloud      { animation: drift var(--t) ease-in-out var(--d) infinite alternate; }

    @keyframes draw        { from { stroke-dashoffset: 1; } to { stroke-dashoffset: 0; } }
    @keyframes fade-up     { from { opacity: 0; transform: translateY(6px); } }
    @keyframes rise        { from { opacity: 0; transform: translateY(16px); } }
    @keyframes appear      { from { opacity: 0; transform: translateX(-10px); } }
    @keyframes label-scale { 0%, $label_end, 100% { transform: none; } $label_peak { transform: scale(1.14); } }
    @keyframes label-tint  { 0%, $label_end, 100% { fill: var(--ink); } $label_peak { fill: var(--accent); } }
    @keyframes label-glow  { 0%, $label_end, 100% { opacity: 0; } $label_peak { opacity: .85; } }
    @keyframes trace       { 0% { stroke-dashoffset: .08; opacity: 0; } $trace_in, $trace_out { opacity: 1; }
                             $trace_end, 100% { stroke-dashoffset: -1; opacity: 0; } }
    @keyframes ripple-grow { 0% { transform: none; } $ripple_end, 100% { transform: scale(4.6); } }
    @keyframes ripple-fade { 0% { opacity: 0; stroke-width: 1.6; } 1% { opacity: .85; stroke-width: 1.6; }
                             $ripple_end, 100% { opacity: 0; stroke-width: .3; } }
    @keyframes breathe     { to { opacity: .2; transform: scale(1.2); } }
    @keyframes twinkle     { 50% { opacity: .12; } }
    @keyframes drift       { from { transform: translateX(calc(-1 * var(--reach))); } to { transform: translateX(var(--reach)); } }

    @media (prefers-reduced-motion: reduce) { * { animation: none !important; } }
  """)


def style(theme: str) -> str:
    css = STYLE.substitute(
        THEMES[theme], sans=SANS, mono=MONO, snow=SNOW, cloud=CLOUD,
        loop=num(LOOP), loop_start=num(LOOP_START), stagger=num(LABEL_STAGGER),
        label_peak=pct(LABEL_GLOW * .45), label_end=pct(LABEL_GLOW),
        trace_at=num(LOOP_START + TRACE_AT), trace_in=pct(.18), trace_out=pct(TRACE_LEN - .18),
        trace_end=pct(TRACE_LEN),
        ripple_at=num(LOOP_START + RIPPLE_AT), ripple_end=pct(RIPPLE_LEN),
    )
    return "\n" + indent(dedent(css).strip(), " " * 6) + "\n    "


def sky(theme: str) -> str:
    cx, cy = ORB
    if theme == "light":
        clouds = "\n    ".join(cloud(c) for c in SKY_CLOUDS)
        return f"""  <g class="ripple"><circle cx="{cx}" cy="{cy}" r="11"/></g>
  <g class="orb">
    <circle class="glow" cx="{cx}" cy="{cy}" r="24" filter="url(#blur)"/>
    <circle class="body" cx="{cx}" cy="{cy}" r="11"/>
  </g>
  <g class="sky">
    {clouds}
  </g>"""
    stars = "\n    ".join(star(s) for s in STARS)
    return f"""  <g class="ripple"><circle cx="{cx}" cy="{cy}" r="10"/></g>
  <g class="orb">
    <circle class="glow" cx="{cx}" cy="{cy}" r="22" filter="url(#blur)"/>
    <circle class="body" cx="{cx}" cy="{cy}" r="10" mask="url(#crescent)"/>
  </g>
  <g class="sky">
    <circle class="haze" cx="{BRIGHT_STAR.x}" cy="{BRIGHT_STAR.y}" r="5" filter="url(#blur)"/>
    {stars}
  </g>"""


def landscape(theme: str) -> str:
    cx, cy = ORB
    d = ridge_path()
    crescent = (f'\n    <mask id="crescent">\n      <circle cx="{cx}" cy="{cy}" r="10" fill="#fff"/>\n'
                f'      <circle cx="{cx + 5}" cy="{cy - 4.5}" r="8.6" fill="#000"/>\n    </mask>') if theme == "dark" else ""
    summits = "\n".join(summit(i, x, y, label) for i, (x, y, label) in enumerate(SUMMITS))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="{VIEW_X} {VIEW_Y} {WIDTH} {HEIGHT}" role="img" aria-labelledby="title">
  <title id="title">{TITLE}</title>
  <!-- generated by scripts/build_assets.py, edit that instead -->
  <defs>
    <style>{style(theme)}</style>
    <filter id="blur" x="-50%" y="-150%" width="200%" height="400%"><feGaussianBlur stdDeviation="3.5"/></filter>
    <path id="ridge-line" pathLength="1" d="{d}"/>{crescent}
  </defs>

  <!-- sky -->
  <text class="meta" x="{LEFT}" y="56">{COORDS}</text>
{sky(theme)}

  <!-- range: the ridge, then two copies for the light that runs along it -->
  <use class="ridge" href="#ridge-line"/>
  <use class="trace halo" href="#ridge-line" filter="url(#blur)"/>
  <use class="trace core" href="#ridge-line"/>

  <!-- summits -->
{summits}

  <!-- caption -->
  <line class="ground" x1="{LEFT}" y1="{GROUND_Y}" x2="{RIGHT}" y2="{GROUND_Y}"/>
  <text class="name" x="{LEFT - 2}" y="{GROUND_Y + 46}">{NAME}</text>
  <text class="meta" x="{RIGHT}" y="{GROUND_Y + 44}" text-anchor="end">{ROLE}</text>
</svg>
"""


# ── Legend SVG ───────────────────────────────────────────────────────────────

LEGEND = [
    ("go", "services · concurrency · systems"),
    ("fastapi", "python apis"),
    ("flutter", "the clients on top"),
]


def legend(theme: str) -> str:
    t = THEMES[theme]
    rows = "\n".join(
        f"""  <g transform="translate(0 {48 + i * 28})">
    <path class="mark" d="M186 -9 L192 1 L180 1 Z"/>
    <text class="key" x="204" y="0">{key}</text>
    <text class="value" x="300" y="0">{value}</text>
  </g>"""
        for i, (key, value) in enumerate(LEGEND))
    summary = "; ".join(f"{k} — {v.replace(' · ', ', ')}" for k, v in LEGEND)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="140" viewBox="{VIEW_X} 0 {WIDTH} 140" role="img" aria-labelledby="title">
  <title id="title">Legend: {summary}</title>
  <!-- generated by scripts/build_assets.py, edit that instead -->
  <defs>
    <style>
      svg    {{ --ink: {t['ink']}; --muted: {t['muted']}; --accent: {t['accent']}; --rule: {t['rule']}; --mono: {MONO}; }}
      .title {{ font: 400 11px var(--mono); letter-spacing: 1.8px; fill: var(--muted); }}
      .key   {{ font: 500 12px var(--mono); letter-spacing: 2px; fill: var(--ink); }}
      .value {{ font: 400 12px var(--mono); letter-spacing: 1px; fill: var(--muted); }}
      .mark  {{ fill: none; stroke: var(--accent); stroke-width: 1.1; stroke-linejoin: miter; }}
      .rule  {{ stroke: var(--rule); stroke-width: 1; }}
    </style>
  </defs>

  <text class="title" x="{LEFT}" y="48">legend</text>
{rows}

  <line class="rule" x1="{LEFT}" y1="132" x2="{RIGHT}" y2="132"/>
</svg>
"""


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    for theme in THEMES:
        for name, build in (("landscape", landscape), ("legend", legend)):
            path = ASSETS / f"{name}-{theme}.svg"
            path.write_text(build(theme), encoding="utf-8")
            print(f"wrote {path.relative_to(ASSETS.parent)}")


if __name__ == "__main__":
    main()
