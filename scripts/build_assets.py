#!/usr/bin/env python3
"""Build the artwork for the GitHub profile README.

Writes four SVGs into assets/:

    landscape-light.svg  landscape-dark.svg   header: sky, ridge, summits, name
    legend-light.svg     legend-dark.svg      key for the three summits

The README picks the light or dark file with <picture>. To change the art,
edit the constants below and run:

    python3 scripts/build_assets.py                # preview into assets/
    python3 scripts/build_assets.py --seed 2026-10-28 --out dist

The sky (cloud layout, wind, stars, shooting stars) is rolled from --seed. A daily
GitHub Action (.github/workflows/sky.yml) builds with the date as the seed and
publishes to the `output` branch, which is what the profile shows.

Animation timeline (seconds after the image loads):

    0.0 – 3.2   intro, once      ridge draws, summits fade up, sun/moon rises
    3.2 – 4.8   sky, once        clouds or stars fade in
    5.0 →       loop, every 12s  labels glow → light runs along the ridge →
                                 ripple leaves the sun/moon → rest
    always      ambient          glow breathes, stars twinkle, clouds sway,
                                 shooting stars fall now and then (dark only)
"""

from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass, replace
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
    scale: float      # 1 = the largest cloud; also sets how far it sways
    reach: float | None = None  # override the sway, for a cloud that must stay over something


# One wind moves every cloud the same way at the same time. Bigger clouds read as
# nearer, so they sway further in the same time and look faster.
WIND_PERIOD = (11, 18)   # seconds for one crossing, rolled daily


def sway(scale: float) -> float:
    """px a cloud of this size travels either side of rest."""
    return 30 * scale - 6


def reach_of(c: Cloud) -> float:
    return sway(c.scale) if c.reach is None else c.reach


# Daily clouds are placed at random inside these rules
CLOUDS_MIN, CLOUDS_EXTRA = 4, 2      # always 4, and on half of all days 2 more
CLOUD_SCALE = (.5, .85)              # the first cloud is always larger, 0.85–1
CLOUD_AREA = (52, 46, 848, 140)      # left, top, right, lowest base: the sky above the labels
CLOUD_GAP = 12                       # px clear between clouds at every point of their sway
KEEP_CLEAR = [(40, 40, 224, 64)]     # boxes no cloud may touch: the coordinates
SUN_CLEAR = 44                       # px from the sun's centre that free clouds stay out of
SUN_CLOUD = Cloud(758, 106, 0.55, reach=4)  # on cloudy days: always trims the sun's lower edge
SUN_CLOUD_CHANCE = .5


@dataclass(frozen=True)
class Star:
    x: float
    y: float
    r: float
    opacity: float
    period: float     # seconds for one twinkle
    delay: float


# Daily stars are scattered at random inside these rules
STAR_COUNT = (10, 13)
STAR_AREA = (56, 52, 844, 152)       # left, top, right, bottom: the sky above the labels
STAR_SPACING = 48                    # px every star keeps from every other, so none clump
MOON_CLEAR = 30                      # px from the moon's centre


@dataclass(frozen=True)
class Meteor:
    x: float          # where the head starts
    y: float
    angle: float      # direction of travel, degrees clockwise from east
    length: float     # tail, px
    width: float
    travel: float     # px the head covers before it burns out
    period: float     # seconds between its appearances
    delay: float      # first appearance, seconds after load


METEOR_COUNT = 10
METEOR_SKY = (52, 62, 848, 150)  # left, top, right, bottom the whole streak must stay inside


def meteors(rng: random.Random) -> list[Meteor]:
    """Shooting stars with seeded-random placement, size and timing.

    An SVG cannot draw random numbers while it plays, so the randomness is baked
    in here. Each meteor repeats on its own period, so together they never fall
    into a rhythm a viewer would notice.
    """
    found: list[Meteor] = []
    while len(found) < METEOR_COUNT:
        # alternate to the right and to the left, always downwards
        angle = rng.uniform(18, 38) if len(found) % 2 == 0 else rng.uniform(142, 162)
        m = Meteor(x=rng.uniform(70, 830), y=rng.uniform(62, 104), angle=angle,
                   length=rng.uniform(36, 84), width=rng.uniform(.8, 1.4), travel=rng.uniform(60, 120),
                   period=rng.uniform(45, 110), delay=0)
        if meteor_fits(m):
            found.append(m)
    # the first falls soon after the sky appears, the rest within the first minute
    delays = [6.5] + sorted(rng.uniform(9, 66) for _ in found[1:])
    return [replace(m, delay=d) for m, d in zip(found, delays)]


def meteor_fits(m: Meteor) -> bool:
    """Stays inside the sky, clear of the moon and the coordinates."""
    dx, dy = math.cos(math.radians(m.angle)), math.sin(math.radians(m.angle))
    tail = (m.x - m.length * dx, m.y - m.length * dy)
    end = (m.x + m.travel * dx, m.y + m.travel * dy)
    left, top, right, bottom = METEOR_SKY
    if not all(left <= x <= right and top <= y <= bottom for x, y in (tail, end)):
        return False
    # sample along the whole path for the moon
    mx, my = ORB
    for i in range(21):
        t = i / 20
        x, y = tail[0] + (end[0] - tail[0]) * t, tail[1] + (end[1] - tail[1]) * t
        if math.hypot(x - mx, y - my) < 34:
            return False
    return True


# ── The day's sky ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Sky:
    clouds: list[Cloud]
    wind: float              # seconds per crossing
    meteors: list[Meteor]
    stars: list[Star]        # brightest first


def roll_sky(seed: str) -> Sky:
    """Everything that changes from day to day, rolled from one seed."""
    rng = random.Random(seed)
    wind = rng.uniform(*WIND_PERIOD)
    clouds = place_clouds(rng, CLOUDS_MIN + (CLOUDS_EXTRA if rng.random() < .5 else 0))
    if rng.random() < SUN_CLOUD_CHANCE:
        clouds.append(SUN_CLOUD)
    return Sky(clouds, wind, meteors(rng), place_stars(rng))


def place_stars(rng: random.Random) -> list[Star]:
    """Spaced-out random stars: mostly small and faint, a few brighter."""
    left, top, right, bottom = STAR_AREA
    count = rng.randint(*STAR_COUNT)
    while True:
        stars: list[Star] = []
        for _ in range(count * 60):
            x, y = round(rng.uniform(left, right)), round(rng.uniform(top, bottom))
            near_moon = math.hypot(x - ORB[0], y - ORB[1]) < MOON_CLEAR
            on_text = any(k[0] <= x <= k[2] and k[1] <= y <= k[3] for k in KEEP_CLEAR)
            crowded = any(math.hypot(x - s.x, y - s.y) < STAR_SPACING for s in stars)
            if near_moon or on_text or crowded:
                continue
            # the first is the bright one; the rest skew small, and brighter stars shine steadier
            size = 1.0 if not stars else rng.random() ** 2 * .75
            stars.append(Star(x=x, y=y, r=.9 + .9 * size, opacity=.5 + .5 * size,
                              period=rng.uniform(3, 5.4), delay=rng.uniform(4.6, 6.5)))
            if len(stars) == count:
                return stars


def cloud_box(c: Cloud) -> tuple[float, float, float, float]:
    """Area a cloud covers across its whole sway: left, top, right, bottom."""
    reach, k = reach_of(c), c.scale
    return c.x - reach, c.y - 27 * k, c.x + 60 * k + reach, c.y


def overlaps(a: tuple, b: tuple, gap: float = 0) -> bool:
    return a[0] < b[2] + gap and b[0] < a[2] + gap and a[1] < b[3] + gap and b[1] < a[3] + gap


def cloud_fits(c: Cloud, taken: list[tuple]) -> bool:
    box = cloud_box(c)
    left, top, right, base = CLOUD_AREA
    if box[0] < left or box[1] < top or box[2] > right or box[3] > base:
        return False
    if any(overlaps(box, k) for k in KEEP_CLEAR) or any(overlaps(box, t, CLOUD_GAP) for t in taken):
        return False
    # nearest point of the box to the sun
    sx, sy = ORB
    nx, ny = min(max(sx, box[0]), box[2]), min(max(sy, box[1]), box[3])
    return math.hypot(sx - nx, sy - ny) > SUN_CLEAR


def place_clouds(rng: random.Random, count: int) -> list[Cloud]:
    """Scatter clouds with no overlaps; the spot over the sun is always held for SUN_CLOUD."""
    left, top, right, base = CLOUD_AREA
    while True:
        taken, placed = [cloud_box(SUN_CLOUD)], []
        for i in range(count):
            for _ in range(400):
                k = rng.uniform(.85, 1.0) if i == 0 else rng.uniform(*CLOUD_SCALE)
                c = Cloud(x=rng.uniform(left, right - 60 * k), y=rng.uniform(top + 27 * k, base), scale=k)
                if cloud_fits(c, taken):
                    taken.append(cloud_box(c))
                    placed.append(c)
                    break
            else:
                break   # this layout boxed itself in; start again
        if len(placed) == count:
            return sorted(placed, key=lambda c: c.x)


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
    return s.replace("0.", ".", 1) if s.lstrip("-").startswith("0.") else s


def pct(seconds: float) -> str:
    return f"{num(seconds / LOOP * 100)}%"


def ridge_path() -> str:
    return "M" + " L".join(f"{x} {y}" for x, y in RIDGE)


def cloud(c: Cloud) -> str:
    k = c.scale
    timing = f"--reach: {num(reach_of(c))}px"
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
        THEMES[theme], sans=SANS, mono=MONO, snow=SNOW, cloud=CLOUD,
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
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--seed", default="preview", help="rolls the sky; the daily build passes the date")
    parser.add_argument("--out", type=Path, default=ASSETS, help="directory to write the SVGs to")
    args = parser.parse_args()

    sky = roll_sky(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        (args.out / f"landscape-{theme}.svg").write_text(landscape(theme, sky), encoding="utf-8")
        (args.out / f"legend-{theme}.svg").write_text(legend(theme), encoding="utf-8")

    sun = "cloud over the sun" if SUN_CLOUD in sky.clouds else "clear sun"
    print(f"sky '{args.seed}': {len(sky.clouds)} clouds, {sun}, wind {sky.wind:.1f}s, "
          f"{len(sky.stars)} stars → {args.out}")


if __name__ == "__main__":
    main()
