"""Turns a Sky into SVG markup. No randomness and no file access live here."""

from __future__ import annotations

from string import Template
from textwrap import dedent, indent

from .config import (
    CLOUD_FILL, COORDS, GROUND_Y, HEIGHT, LABEL_GLOW, LABEL_STAGGER, LABEL_Y, LEFT, LEGEND, LOOP,
    LOOP_START, MONO, NAME, ORB, RIDGE, RIGHT, RIPPLE_AT, RIPPLE_LEN, ROLE, SANS, SNOW, SUMMITS,
    THEMES, TITLE, TRACE_AT, TRACE_LEN, VIEW_X, VIEW_Y, WIDTH,
)
from .models import Cloud, Meteor, Sky, Star


# ── Formatting ───────────────────────────────────────────────────────────────

def num(v: float) -> str:
    """Shortest clean form of a number: 12.0 → 12, 0.50 → .5"""
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s.replace("0.", ".", 1) if s.lstrip("-").startswith("0.") else s


def pct(seconds: float) -> str:
    return f"{num(seconds / LOOP * 100)}%"


def ridge_path() -> str:
    return "M" + " L".join(f"{x} {y}" for x, y in RIDGE)


# ── Elements ─────────────────────────────────────────────────────────────────

def cloud(c: Cloud) -> str:
    k = c.scale
    timing = f"--reach: {num(c.reach)}px"
    parts = [
        f'<rect x="{num(c.x)}" y="{num(c.y - 10*k)}" width="{num(60*k)}" height="{num(10*k)}" rx="{num(5*k)}"/>',
        f'<circle cx="{num(c.x + 18*k)}" cy="{num(c.y - 10*k)}" r="{num(10*k)}"/>',
        f'<circle cx="{num(c.x + 34*k)}" cy="{num(c.y - 14*k)}" r="{num(13*k)}"/>',
        f'<circle cx="{num(c.x + 48*k)}" cy="{num(c.y - 9*k)}" r="{num(8*k)}"/>',
    ]
    inner = "\n      ".join(parts)
    return f'<g class="cloud" style="{timing}">\n      {inner}\n    </g>'


def star(s: Star) -> str:
    timing = f"--t: {num(s.period)}s; --d: {num(s.delay)}s; opacity: {num(s.opacity)}"
    return f'<circle class="star" cx="{s.x}" cy="{s.y}" r="{num(s.r)}" style="{timing}"/>'


def meteor(m: Meteor) -> str:
    timing = f"--travel: {num(m.travel)}px; --t: {num(m.period)}s; --d: {num(m.delay)}s"
    return f"""<g transform="translate({num(m.x)} {num(m.y)}) rotate({num(m.angle)})">
      <g class="meteor" style="{timing}">
        <rect class="tail" x="{num(-m.length)}" y="{num(-m.width / 2)}" width="{num(m.length)}" height="{num(m.width)}" rx="{num(m.width / 2)}"/>
        <circle class="head" r="{num(m.width * .75)}"/>
      </g>
    </g>"""


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
    .cloud      { animation: drift ${wind}s ease-in-out -${wind_half}s infinite alternate; }

    /* shooting stars (dark only): the tail stretches out, the head streaks and burns out */
    .meteor       { opacity: 0; animation: meteor var(--t) linear var(--d) infinite; }
    .meteor .tail { fill: url(#meteor-tail); transform-box: fill-box; transform-origin: right center;
                    animation: meteor-tail var(--t) ease-out var(--d) infinite; }
    .meteor .head { fill: $snow; }

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
    @keyframes meteor      { 0% { opacity: 0; transform: none; } .25% { opacity: 1; }
                             1.3%, 100% { opacity: 0; transform: translateX(var(--travel)); } }
    @keyframes meteor-tail { 0% { transform: scaleX(.15); } .6%, 100% { transform: none; } }
    @keyframes drift       { from { transform: translateX(calc(-1 * var(--reach))); } to { transform: translateX(var(--reach)); } }

    @media (prefers-reduced-motion: reduce) { * { animation: none !important; } }
  """)


def style(theme: str, sky: Sky) -> str:
    css = STYLE.substitute(
        THEMES[theme], sans=SANS, mono=MONO, snow=SNOW, cloud=CLOUD_FILL,
        loop=num(LOOP), loop_start=num(LOOP_START), stagger=num(LABEL_STAGGER),
        wind=num(sky.wind), wind_half=num(sky.wind / 2),
        label_peak=pct(LABEL_GLOW * .45), label_end=pct(LABEL_GLOW),
        trace_at=num(LOOP_START + TRACE_AT), trace_in=pct(.18), trace_out=pct(TRACE_LEN - .18),
        trace_end=pct(TRACE_LEN),
        ripple_at=num(LOOP_START + RIPPLE_AT), ripple_end=pct(RIPPLE_LEN),
    )
    return "\n" + indent(dedent(css).strip(), " " * 6) + "\n    "


def sky_layer(theme: str, sky: Sky) -> str:
    cx, cy = ORB
    if theme == "light":
        clouds = "\n    ".join(cloud(c) for c in sky.clouds)
        return f"""  <g class="ripple"><circle cx="{cx}" cy="{cy}" r="11"/></g>
  <g class="orb">
    <circle class="glow" cx="{cx}" cy="{cy}" r="24" filter="url(#blur)"/>
    <circle class="body" cx="{cx}" cy="{cy}" r="11"/>
  </g>
  <g class="sky">
    {clouds}
  </g>"""
    stars = "\n    ".join(star(s) for s in sky.stars)
    bright = sky.stars[0]
    shooting = "\n    ".join(meteor(m) for m in sky.meteors)
    return f"""  <g class="ripple"><circle cx="{cx}" cy="{cy}" r="10"/></g>
  <g class="orb">
    <circle class="glow" cx="{cx}" cy="{cy}" r="22" filter="url(#blur)"/>
    <circle class="body" cx="{cx}" cy="{cy}" r="10" mask="url(#crescent)"/>
  </g>
  <g class="sky">
    <circle class="haze" cx="{bright.x}" cy="{bright.y}" r="5" filter="url(#blur)"/>
    {stars}
    {shooting}
  </g>"""


def landscape(theme: str, sky: Sky) -> str:
    cx, cy = ORB
    d = ridge_path()
    night_defs = f"""
    <mask id="crescent">
      <circle cx="{cx}" cy="{cy}" r="10" fill="#fff"/>
      <circle cx="{cx + 5}" cy="{cy - 4.5}" r="8.6" fill="#000"/>
    </mask>
    <linearGradient id="meteor-tail">
      <stop offset="0" stop-color="{SNOW}" stop-opacity="0"/>
      <stop offset="1" stop-color="{SNOW}" stop-opacity=".85"/>
    </linearGradient>""" if theme == "dark" else ""
    summits = "\n".join(summit(i, x, y, label) for i, (x, y, label) in enumerate(SUMMITS))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="{VIEW_X} {VIEW_Y} {WIDTH} {HEIGHT}" role="img" aria-labelledby="title">
  <title id="title">{TITLE}</title>
  <!-- generated by scripts/build_assets.py, edit that instead -->
  <defs>
    <style>{style(theme, sky)}</style>
    <filter id="blur" x="-50%" y="-150%" width="200%" height="400%"><feGaussianBlur stdDeviation="3.5"/></filter>
    <path id="ridge-line" pathLength="1" d="{d}"/>{night_defs}
  </defs>

  <!-- sky -->
  <text class="meta" x="{LEFT}" y="56">{COORDS}</text>
{sky_layer(theme, sky)}

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
