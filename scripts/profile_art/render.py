"""Turns a Sky into SVG markup. No randomness and no file access live here."""

from __future__ import annotations

import math
from string import Template
from textwrap import dedent, indent

from .config import (
    AURORA_COLORS, CANOPY, CLOUD_FILL, CONTRAIL, COORDS, GLIDER_WING, GROUND_Y, HEIGHT, LABEL_GLOW,
    LABEL_STAGGER, LABEL_Y, LEFT, LEGEND, MONO, MOON_R, MOON_TILT, NAME, ORB, RIDGE, RIGHT, RIPPLE_AT,
    RIPPLE_LEN, ROLE, SANS, SATELLITE_HULL, SATELLITE_PANEL, SATELLITE_TRIM, SATELLITE_TUMBLE,
    SEQUENCE_START, SNOW, SUMMITS, THEMES, TITLE, TRACE_AT, TRACE_LEN, UFO_COLORS,
    VIEW_X, VIEW_Y, VISIT_FIRST, VISITOR_INK, WIDTH,
)
from .models import Cloud, Meteor, Moon, Ribbon, Satellite, Sky, Star, Ufo, Visit

Point = tuple[float, float]


# ── Formatting ───────────────────────────────────────────────────────────────

def num(v: float) -> str:
    """Shortest clean form of a number: 12.0 → 12, 0.50 → .5"""
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s.replace("0.", ".", 1) if s.lstrip("-").startswith("0.") else s


def share(seconds: float, cycle: float) -> str:
    """A moment in a looping animation, as a keyframe percentage."""
    return f"{num(seconds / cycle * 100)}%"


def ridge_path() -> str:
    return "M" + " L".join(f"{x} {y}" for x, y in RIDGE)


def above_ridge_path() -> str:
    """Everything above the ridge line: the aurora glows and day visitors fly only here."""
    edge = " L".join(f"{x} {y}" for x, y in reversed(RIDGE))
    return f"M{VIEW_X} {VIEW_Y} H{VIEW_X + WIDTH} V{RIDGE[-1][1]} L{edge} H{VIEW_X} V{VIEW_Y}Z"


def smooth(points: list[Point]) -> str:
    """Cubic segments through the points (Catmull-Rom), after an initial move to points[0]."""
    ext = [points[0], *points, points[-1]]
    segments = []
    for i in range(1, len(ext) - 2):
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        segments.append(f"C{num(x1 + (x2 - x0) / 6)} {num(y1 + (y2 - y0) / 6)} "
                        f"{num(x2 - (x3 - x1) / 6)} {num(y2 - (y3 - y1) / 6)} {num(x2)} {num(y2)}")
    return " ".join(segments)


# ── Sky elements ─────────────────────────────────────────────────────────────

def cloud(c: Cloud) -> str:
    k = c.scale
    parts = [
        f'<rect x="{num(c.x)}" y="{num(c.y - 10*k)}" width="{num(60*k)}" height="{num(10*k)}" rx="{num(5*k)}"/>',
        f'<circle cx="{num(c.x + 18*k)}" cy="{num(c.y - 10*k)}" r="{num(10*k)}"/>',
        f'<circle cx="{num(c.x + 34*k)}" cy="{num(c.y - 14*k)}" r="{num(13*k)}"/>',
        f'<circle cx="{num(c.x + 48*k)}" cy="{num(c.y - 9*k)}" r="{num(8*k)}"/>',
    ]
    inner = "\n      ".join(parts)
    return f'<g class="cloud" style="--reach: {num(c.reach)}px">\n      {inner}\n    </g>'


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


def moon_shape(m: Moon) -> str:
    """The lit part of the disc: the limb on the lit side, closed by the terminator,
    an ellipse whose half-width shrinks to nothing at first and last quarter."""
    (cx, cy), r = ORB, MOON_R
    top, bottom = f"{cx} {cy - r}", f"{cx} {cy + r}"
    limb = 1 if m.waxing else 0                      # waxing is lit on the right
    terminator = 1 if (m.lit > .5) == m.waxing else 0
    d = f"M{top} A{r} {r} 0 0 {limb} {bottom} A{num(abs(1 - 2 * m.lit) * r)} {r} 0 0 {terminator} {top}Z"
    return f'<path class="body" transform="rotate({MOON_TILT} {cx} {cy})" d="{d}"/>'


def ribbon(i: int, rb: Ribbon) -> str:
    """The mask holds the lit stretch of sky still while the folds flow through it."""
    lower = [(x, y + rb.thickness) for x, y in reversed(rb.top)]
    (x0, y0), (x1, y1) = rb.top[0], lower[0]
    d = f"M{num(x0)} {num(y0)} {smooth(rb.top)} L{num(x1)} {num(y1)} {smooth(lower)}Z"
    wave = rb.wave if rb.flow > 0 else -rb.wave
    flow = f"--wave: {num(wave)}px; --t: {num(abs(rb.flow))}s; --d: -{num(i * 3.5)}s"
    return f"""<g mask="url(#aurora-window-{i})" opacity="{num(rb.opacity)}">
        <g class="aurora" style="{flow}"><path fill="url(#aurora-{i})" d="{d}"/></g>
      </g>"""


def satellite(s: Satellite) -> str:
    """A cylinder body between two solar-panel wings, leaning as one piece. The
    outer group carries it across, the inner one lifts it along the arc."""
    motion = f"--dx: {num(s.dx)}px; --dy: {num(s.dy)}px; --d: {num(s.start)}s"
    return f"""<g transform="translate({num(s.x)} {num(s.y)})">
    <g class="satellite" style="{motion}">
      <g class="orbit" style="--arc: {num(-s.arc)}px">
        <g transform="rotate({num(s.lean)})">
          <g class="craft">
            <rect class="panel" x="-11" y="-2" width="7" height="4" rx=".4"/>
            <rect class="panel" x="4" y="-2" width="7" height="4" rx=".4"/>
            <path class="trim" d="M-7.5 -2 V2 M7.5 -2 V2 M-4 0 H-2 M2 0 H4"/>
            <rect class="hull" x="-2" y="-3.2" width="4" height="6.4" rx="1.4"/>
          </g>
        </g>
      </g>
    </g>
  </g>"""


def ufo(u: Ufo) -> str:
    """A saucer with a dome, an underglow and three blinking lights."""
    motion = f"--rise: {num(u.rise)}px; --dx: {num(u.dx)}px; --dy: {num(u.dy)}px; --d: {num(u.start)}s"
    lights = "".join(f'<circle class="light" cx="{x}" cy=".7" r=".75" style="animation-delay: -{num(i * .3)}s"/>'
                     for i, x in enumerate((-5, 0, 5)))
    return f"""<g transform="translate({num(u.x)} {num(u.y)})">
      <g class="ufo" style="{motion}">
        <g class="hover">
          <ellipse class="underglow" cy="3.5" rx="7" ry="2.5" filter="url(#blur)"/>
          <path class="dome" d="M-4.2 -1.6 A4.2 3.8 0 0 1 4.2 -1.6 Z"/>
          <ellipse class="saucer" rx="10" ry="2.6"/>
          {lights}
        </g>
      </g>
    </g>"""


# ── Day visitors ─────────────────────────────────────────────────────────────
# Each is drawn facing right around (0, 0) and mirrored when it flies left.

def birds(v: Visit) -> str:
    wings = []
    for i, (ox, oy, k) in enumerate(v.flock):
        d = (f"M{num(ox - 5*k)} {num(oy)} Q{num(ox - 2.5*k)} {num(oy - 3*k)} {num(ox)} {num(oy)} "
             f"Q{num(ox + 2.5*k)} {num(oy - 3*k)} {num(ox + 5*k)} {num(oy)}")
        wings.append(f'<path class="bird" style="animation-delay: -{num(i * .17)}s" d="{d}"/>')
    return "\n          ".join(wings)


def parachute() -> str:
    return """<g class="swing">
            <path class="chute" d="M-8 -14 Q-8 -22 0 -22 Q8 -22 8 -14 Q4 -16 0 -14 Q-4 -16 -8 -14 Z"/>
            <path class="lines" d="M-8 -14 L0 0 M8 -14 L0 0 M0 -14 V0"/>
            <path class="diver" d="M0 0 V3.4 M-1.6 1.2 H1.6"/>
            <circle class="pilot" cy="-.8" r="1.2"/>
          </g>"""


def hang_glider() -> str:
    return """<g class="bank">
            <path class="wing" d="M-11 -6 Q0 -10 11 -6 L0 -4 Z"/>
            <path class="lines" d="M-3.5 -4.6 L-1.5 0 H1.5 L3.5 -4.6 M0 -4.4 V-1"/>
            <rect class="pilot" x="-3" y="-1.6" width="6" height="1.5" rx=".75"/>
          </g>"""


def plane() -> str:
    return """<rect class="contrail" x="-150" y=".1" width="143" height="1" rx=".5"/>
          <path class="plane" d="M-6 0 H5 Q7 0 7 .6 Q7 1.2 5 1.2 H-5 Z M-6 0 L-7.5 -2.6 H-5.4 L-3.6 0 Z M-1 .8 L-3 2.6 H-1.6 L1.6 .8 Z"/>"""


def visitor(v: Visit) -> str:
    r = v.route
    shape = {"birds": lambda: birds(v), "parachute": parachute, "glider": hang_glider, "plane": plane}[v.kind]()
    if v.kind == "plane":   # nose up when climbing, down when descending
        shape = f'<g transform="rotate({num(math.degrees(math.atan2(r.dy, abs(r.dx))))})">\n          {shape}\n        </g>'
    if r.dx < 0:
        shape = f'<g transform="scale(-1 1)">\n          {shape}\n        </g>'
    motion = f"--dx: {num(r.dx)}px; --dy: {num(r.dy)}px; --d: {num(VISIT_FIRST + v.start)}s"
    return f"""<g transform="translate({num(r.x)} {num(r.y)})">
      <g class="visitor {v.kind}" style="{motion}">
        {shape}
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


# ── Styles ───────────────────────────────────────────────────────────────────

COMMON_STYLE = Template("""
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

    /* 1 · intro, plays once */
    .ridge  { stroke-dasharray: 1; animation: draw 2.6s cubic-bezier(.6, .05, .3, 1) both; }
    .summit { animation: fade-up .8s ease-out calc(1.6s + var(--i) * .4s) backwards; }
    .orb    { animation: rise 3s ease-out backwards; }
    .sky    { animation: appear 1.6s ease-out 3.2s backwards; }

    /* 2 · once, after the intro: labels glow in turn, light runs along the ridge,
       a ripple leaves the sun / moon; then the header rests */
    .pulse        { transform-box: fill-box; transform-origin: center;
                    animation: label-scale ${glow}s ease-in-out calc(${start}s + var(--i) * ${stagger}s); }
    .pulse .label { animation: label-tint ${glow}s ease-in-out; animation-delay: inherit; }
    .pulse .halo  { fill: var(--accent); opacity: 0; animation-name: label-glow; }

    .trace      { fill: none; stroke-linecap: round; stroke-dasharray: .08 1.2; stroke-dashoffset: .08; opacity: 0;
                  animation: trace ${trace_len}s ease-in-out ${trace_at}s; }
    .trace.core { stroke: var(--ink); stroke-width: 2; }
    .trace.halo { stroke: var(--accent); stroke-width: 5; }

    .ripple        { transform-box: fill-box; transform-origin: center;
                     animation: ripple-grow ${ripple_len}s cubic-bezier(.2, .6, .3, 1) ${ripple_at}s; }
    .ripple circle { fill: none; stroke: var(--ripple); stroke-width: 1.6; vector-effect: non-scaling-stroke; opacity: 0;
                     animation: ripple-fade ${ripple_len}s linear ${ripple_at}s; }

    /* ambient */
    .glow { opacity: .1; transform-box: fill-box; transform-origin: center;
            animation: breathe 9s ease-in-out 3s infinite alternate; }

    @keyframes draw        { from { stroke-dashoffset: 1; } to { stroke-dashoffset: 0; } }
    @keyframes fade-up     { from { opacity: 0; transform: translateY(6px); } }
    @keyframes rise        { from { opacity: 0; transform: translateY(16px); } }
    @keyframes appear      { from { opacity: 0; transform: translateX(-10px); } }
    @keyframes label-scale { 45% { transform: scale(1.14); } }
    @keyframes label-tint  { 45% { fill: var(--accent); } }
    @keyframes label-glow  { 45% { opacity: .85; } }
    @keyframes trace       { 0% { stroke-dashoffset: .08; opacity: 0; } 7.5%, 92.5% { opacity: 1; }
                             100% { stroke-dashoffset: -1; opacity: 0; } }
    @keyframes ripple-grow { to { transform: scale(4.6); } }
    @keyframes ripple-fade { 0% { opacity: 0; stroke-width: 1.6; } 4.5% { opacity: .85; stroke-width: 1.6; }
                             100% { opacity: 0; stroke-width: .3; } }
    @keyframes breathe     { to { opacity: .2; transform: scale(1.2); } }
    @keyframes drift       { from { transform: translateX(calc(-1 * var(--reach))); } to { transform: translateX(var(--reach)); } }
""")

DAY_STYLE = Template("""
    /* day: clouds sway in one wind */
    .cloud { fill: $cloud; animation: drift ${wind}s ease-in-out -${wind_half}s infinite alternate; }

    /* day: birds, the parachute, the hang glider and the plane take turns crossing */
    .visitor           { opacity: 0; animation: none ${cycle}s linear var(--d) infinite; }
    .visitor.birds     { animation-name: fly-birds; }
    .visitor.parachute { animation-name: fly-parachute; }
    .visitor.glider    { animation-name: fly-glider; }
    .visitor.plane     { animation-name: fly-plane; }
    .bird  { fill: none; stroke: $ink_day; stroke-width: 1.1; stroke-linecap: round; stroke-linejoin: round;
             transform-box: fill-box; transform-origin: center; animation: flap .5s ease-in-out infinite alternate; }
    .swing { transform-box: fill-box; transform-origin: 50% 0; animation: sway 3.4s ease-in-out infinite alternate; }
    .bank  { transform-box: fill-box; transform-origin: center; animation: bank 5s ease-in-out infinite alternate; }
    .chute { fill: $canopy; }
    .wing  { fill: $wing; }
    .lines, .diver { fill: none; stroke: $ink_day; stroke-width: .45; stroke-linecap: round; }
    .diver { stroke-width: .9; }
    .pilot, .plane { fill: $ink_day; }
    .contrail { fill: url(#contrail); }

    $fly_birds
    $fly_parachute
    $fly_glider
    $fly_plane
    @keyframes flap { to { transform: scaleY(-.45); } }
    @keyframes sway { from { transform: rotate(-5deg); } to { transform: rotate(5deg); } }
    @keyframes bank { from { transform: rotate(-3deg); } to { transform: rotate(3deg); } }
""")

NIGHT_STYLE = Template("""
    /* night: stars twinkle out of step, the brightest has a haze */
    .star, .haze { fill: $snow; }
    .haze { opacity: .18; }
    .star { animation: twinkle var(--t) ease-in-out var(--d) infinite; }

    /* night: shooting stars stretch out, streak and burn out */
    .meteor       { opacity: 0; animation: meteor var(--t) linear var(--d) infinite; }
    .meteor .tail { fill: url(#meteor-tail); transform-box: fill-box; transform-origin: right center;
                    animation: meteor-tail var(--t) ease-out var(--d) infinite; }
    .meteor .head { fill: $snow; }

    /* night: aurora folds flow sideways and shimmer; a satellite arcs over now and then */
    .aurora      { animation: flow var(--t) linear infinite; }
    .aurora path { animation: shimmer 7s ease-in-out var(--d) infinite alternate; }
    .satellite   { opacity: 0; animation: satellite ${sat_cycle}s linear var(--d) infinite; }
    .orbit       { animation: orbit ${sat_cycle}s linear var(--d) infinite; }
    .craft       { transform-box: fill-box; transform-origin: center; animation: tumble 16s ease-in-out infinite alternate; }
    .craft .hull  { fill: $sat_hull; }
    .craft .panel { fill: $sat_panel; stroke: $sat_trim; stroke-width: .4; }
    .craft .trim  { fill: none; stroke: $sat_trim; stroke-width: .5; }


    @keyframes twinkle     { 50% { opacity: .12; } }
    @keyframes meteor      { 0% { opacity: 0; transform: none; } .25% { opacity: 1; }
                             1.3%, 100% { opacity: 0; transform: translateX(var(--travel)); } }
    @keyframes meteor-tail { 0% { transform: scaleX(.15); } .6%, 100% { transform: none; } }
    @keyframes flow        { to { transform: translateX(var(--wave)); } }
    @keyframes shimmer     { from { opacity: .55; } to { opacity: 1; } }
    @keyframes tumble      { from { transform: rotate(-${tumble}deg); } to { transform: rotate(${tumble}deg); } }
    $satellite
    $orbit
""")

UFO_STYLE = Template("""
    /* day and night: UFOs rise from behind the ridge, park, then leave for space */
    .ufo       { opacity: 0; transform-box: fill-box; transform-origin: center;
                 animation: ufo ${cycle}s linear var(--d) infinite; }
    .hover     { animation: bob 1.8s ease-in-out infinite alternate; }
    .saucer    { fill: $hull; }
    .dome      { fill: $dome; opacity: .8; }
    .underglow { fill: $dome; opacity: .35; }
    .light     { fill: $light; animation: blink .9s steps(2) infinite; }

    $visit
    @keyframes bob   { from { transform: translateY(-1.5px); } to { transform: translateY(1.5px); } }
    @keyframes blink { 50% { opacity: .2; } }
""")

REDUCED_MOTION = "\n    @media (prefers-reduced-motion: reduce) { * { animation: none !important; } }\n"


def crossing(name: str, duration: float, cycle: float, peak: float = 1) -> str:
    """Keyframes for something that fades in, crosses for `duration` seconds and
    fades out, then waits out the rest of a `cycle`-second loop."""
    fade = 1.0
    return (f"@keyframes {name} {{ 0% {{ opacity: 0; transform: none; }} "
            f"{share(fade, cycle)}, {share(duration - fade, cycle)} {{ opacity: {num(peak)}; }} "
            f"{share(duration, cycle)}, 100% {{ opacity: 0; transform: translate(var(--dx), var(--dy)); }} }}")


def arc(name: str, duration: float, cycle: float) -> str:
    """Keyframes that lift something by var(--arc) and set it back down over
    `duration` seconds: quadratic easing either side of the top traces a parabola."""
    rise, fall = "cubic-bezier(.25, .46, .45, .94)", "cubic-bezier(.55, .085, .68, .53)"
    return (f"@keyframes {name} {{ 0% {{ transform: none; animation-timing-function: {rise}; }} "
            f"{share(duration / 2, cycle)} {{ transform: translateY(var(--arc)); animation-timing-function: {fall}; }} "
            f"{share(duration, cycle)}, 100% {{ transform: none; }} }}")


def ufo_visit(rise: float, park: float, leave: float, cycle: float) -> str:
    """Keyframes: up from behind the ridge (easing to a stop), parked, then away
    with growing speed, shrinking as it goes."""
    up, away = "cubic-bezier(.2, .7, .3, 1)", "cubic-bezier(.6, 0, .9, .4)"
    return (f"@keyframes ufo {{ 0% {{ opacity: 1; transform: translateY(var(--rise)); animation-timing-function: {up}; }} "
            f"{share(rise, cycle)} {{ opacity: 1; transform: none; }} "
            f"{share(rise + park, cycle)} {{ opacity: 1; transform: none; animation-timing-function: {away}; }} "
            f"{share(rise + park + leave, cycle)}, 100% {{ opacity: 0; transform: translate(var(--dx), var(--dy)) scale(.2); }} }}")


def style(theme: str, sky: Sky) -> str:
    css = COMMON_STYLE.substitute(
        THEMES[theme], sans=SANS, mono=MONO,
        start=num(SEQUENCE_START), glow=num(LABEL_GLOW), stagger=num(LABEL_STAGGER),
        trace_at=num(SEQUENCE_START + TRACE_AT), trace_len=num(TRACE_LEN),
        ripple_at=num(SEQUENCE_START + RIPPLE_AT), ripple_len=num(RIPPLE_LEN),
    )
    if theme == "light":
        css += DAY_STYLE.substitute(
            cloud=CLOUD_FILL, wind=num(sky.wind), wind_half=num(sky.wind / 2),
            cycle=num(sky.visit_cycle), ink_day=VISITOR_INK, canopy=CANOPY, wing=GLIDER_WING,
            **{f"fly_{kind}": crossing(f"fly-{kind}", sky.flight[kind], sky.visit_cycle) for kind in sky.flight},
        )
    else:
        css += NIGHT_STYLE.substitute(
            snow=SNOW, sat_cycle=num(sky.satellite_cycle), tumble=num(SATELLITE_TUMBLE),
            sat_hull=SATELLITE_HULL, sat_panel=SATELLITE_PANEL, sat_trim=SATELLITE_TRIM,
            satellite=crossing("satellite", sky.satellite_pass, sky.satellite_cycle),
            orbit=arc("orbit", sky.satellite_pass, sky.satellite_cycle),
        )
    css += UFO_STYLE.substitute(UFO_COLORS[theme], cycle=num(sky.ufo_cycle),
                                visit=ufo_visit(*sky.ufo_times, sky.ufo_cycle))
    css += REDUCED_MOTION
    return "\n" + indent(dedent(css).strip(), " " * 6) + "\n    "


# ── Landscape SVG ────────────────────────────────────────────────────────────

def defs(theme: str, sky: Sky) -> str:
    """Gradients, masks, clips and filters only the given theme uses."""
    if theme == "light":
        return f"""
    <linearGradient id="contrail">
      <stop offset="0" stop-color="{CONTRAIL}" stop-opacity="0"/>
      <stop offset="1" stop-color="{CONTRAIL}" stop-opacity=".9"/>
    </linearGradient>"""
    return f"""
    <linearGradient id="meteor-tail">
      <stop offset="0" stop-color="{SNOW}" stop-opacity="0"/>
      <stop offset="1" stop-color="{SNOW}" stop-opacity=".85"/>
    </linearGradient>
{"".join(aurora_gradient(i, color) for i, color in enumerate(AURORA_COLORS))}
    <linearGradient id="fade-ends">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/>
      <stop offset=".3" stop-color="#fff"/>
      <stop offset=".7" stop-color="#fff"/>
      <stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>{"".join(aurora_window(i, rb) for i, rb in enumerate(sky.aurora))}
    <filter id="haze" x="-10%" y="-60%" width="120%" height="220%"><feGaussianBlur stdDeviation="6"/></filter>"""


def aurora_gradient(i: int, color: str) -> str:
    """Brightest towards the lower edge and fading upwards, like a real curtain."""
    return f"""
    <linearGradient id="aurora-{i}" x2="0" y2="1">
      <stop offset="0" stop-color="{color}" stop-opacity="0"/>
      <stop offset=".7" stop-color="{color}"/>
      <stop offset="1" stop-color="{color}" stop-opacity=".15"/>
    </linearGradient>"""


def aurora_window(i: int, rb: Ribbon) -> str:
    """Limits a curtain to its stretch of sky, fading in and out at the ends."""
    left, right = rb.span
    return f"""
    <mask id="aurora-window-{i}" maskUnits="userSpaceOnUse">
      <rect x="{num(left)}" y="{VIEW_Y}" width="{num(right - left)}" height="{HEIGHT}" fill="url(#fade-ends)"/>
    </mask>"""


def ufo_layer(sky: Sky) -> str:
    """Clipped to the sky, so each UFO comes up from behind the ridge."""
    ufos = "\n    ".join(ufo(u) for u in sky.ufos)
    return f"""<g class="ufos" clip-path="url(#above-ridge)">
    {ufos}
  </g>"""


def day_sky(sky: Sky) -> str:
    (cx, cy), clouds = ORB, "\n    ".join(cloud(c) for c in sky.clouds)
    visitors = "\n    ".join(visitor(v) for v in sky.visits)
    return f"""  <g class="ripple"><circle cx="{cx}" cy="{cy}" r="11"/></g>
  <g class="orb">
    <circle class="glow" cx="{cx}" cy="{cy}" r="24" filter="url(#blur)"/>
    <circle class="body" cx="{cx}" cy="{cy}" r="11"/>
  </g>
  <g class="sky">
    {clouds}
  </g>
  <g class="visitors" clip-path="url(#above-ridge)">
    {visitors}
  </g>
  {ufo_layer(sky)}"""


def night_sky(sky: Sky) -> str:
    (cx, cy), bright = ORB, sky.stars[0]
    aurora = "\n      ".join(ribbon(i, rb) for i, rb in enumerate(sky.aurora))
    stars = "\n    ".join(star(s) for s in sky.stars)
    shooting = "\n    ".join(meteor(m) for m in sky.meteors)
    satellites = "\n  ".join(satellite(s) for s in sky.satellites)

    return f"""  <g class="ripple"><circle cx="{cx}" cy="{cy}" r="{MOON_R}"/></g>
  <g class="orb">
    <circle class="glow" cx="{cx}" cy="{cy}" r="22" filter="url(#blur)"/>
    {moon_shape(sky.moon)}
  </g>
  <g class="sky">
    <g clip-path="url(#above-ridge)">
      <g filter="url(#haze)">
      {aurora}
      </g>
    </g>
    <circle class="haze" cx="{bright.x}" cy="{bright.y}" r="5" filter="url(#blur)"/>
    {stars}
    {shooting}
  </g>
  {ufo_layer(sky)}
  {satellites}"""


def landscape(theme: str, sky: Sky) -> str:
    summits = "\n".join(summit(i, x, y, label) for i, (x, y, label) in enumerate(SUMMITS))
    sky_layer = day_sky(sky) if theme == "light" else night_sky(sky)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="{VIEW_X} {VIEW_Y} {WIDTH} {HEIGHT}" role="img" aria-labelledby="title">
  <title id="title">{TITLE}</title>
  <!-- generated by scripts/build_assets.py, edit that instead -->
  <defs>
    <style>{style(theme, sky)}</style>
    <filter id="blur" x="-50%" y="-150%" width="200%" height="400%"><feGaussianBlur stdDeviation="3.5"/></filter>
    <path id="ridge-line" pathLength="1" d="{ridge_path()}"/>
    <clipPath id="above-ridge"><path d="{above_ridge_path()}"/></clipPath>{defs(theme, sky)}
  </defs>

  <!-- sky -->
  <text class="meta" x="{LEFT}" y="56">{COORDS}</text>
{sky_layer}

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
