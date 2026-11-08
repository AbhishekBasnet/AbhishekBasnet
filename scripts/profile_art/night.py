"""The night visitors and the comet: what they look like and how they move.

    lanterns(visit), balloon()   the visitors, drawn around (0, 0)
    comet(comet)                                             the comet
    night_visitor_style(sky)                                 their CSS
    night_glows()                                            their soft glows, as gradients

Every glow here is a gradient rather than a blur filter, and everything moves by
position and fade alone, so the night stays light on the GPU.
"""

from __future__ import annotations

from string import Template

from .config import (
    BALLOON_HOVER, COMET_ION, BALLOON_SIZE, LANTERN_GLOW, LANTERN_PAPER, LANTERN_SIZE, NIGHT_DARK,
    NIGHT_INK, SNOW,
)
from .keyframes import crossing, num, share
from .models import Comet, Sky, Visit



# ── The visitors ─────────────────────────────────────────────────────────────

def lanterns(visit: Visit) -> str:
    """Paper sky lanterns rising together, each glowing, flickering and swaying."""
    return "".join(
        f'<g transform="translate({num(offset_x)} {num(offset_y)}) scale({num(size * LANTERN_SIZE)})">'
        f'<g class="lantern" style="animation-delay: -{num(n * .9)}s">'
        f'<circle class="halo" r="5" fill="url(#lantern-glow)"/>'
        f'<path class="paper" d="M-1.5 -2.4 L1.5 -2.4 L1.2 1.8 L-1.2 1.8Z"/>'
        f'<circle class="flame" cy="1.4" r=".45"/></g></g>'
        for n, (offset_x, offset_y, size) in enumerate(visit.flock))


def balloon() -> str:
    """A hot air balloon bobbing gently, its burner alight the whole way: the flame
    flickers, and its glow lights the envelope from inside, brightest on the climb
    and dimming on the way down. The flame sits just under the envelope's mouth,
    above the basket, where a real burner is. Drawn with the basket at (0, 0) and
    scaled up by BALLOON_SIZE."""
    return f"""<g class="drift"><g transform="scale({num(BALLOON_SIZE)})">
            <path class="envelope" d="M0 -23 C6.5 -23 7.5 -15 4.6 -10.5 L2 -7 H-2 L-4.6 -10.5 C-7.5 -15 -6.5 -23 0 -23Z"/>
            <path class="seams" d="M0 -23 V-7 M-3.6 -21.6 Q-4.2 -14 -1.4 -7 M3.6 -21.6 Q4.2 -14 1.4 -7"/>
            <circle class="flare" cy="-13" r="10" fill="url(#balloon-flare)"/>
            <path class="burner" d="M0 -7.6 Q1.1 -5.9 0 -4.6 Q-1.1 -5.9 0 -7.6Z"/>
            <path class="ropes" d="M-2 -7 L-1.4 -3.4 M2 -7 L1.4 -3.4"/>
            <rect class="basket" x="-1.6" y="-3.4" width="3.2" height="2.4" rx=".3"/>
          </g></g>"""


NIGHT_SHAPES = {"lanterns": lanterns, "balloon": lambda visit: balloon()}


# ── The comet ────────────────────────────────────────────────────────────────

def comet(c: Comet) -> str:
    """A soft dust tail fading behind a bright head, a fainter blue ion tail
    splitting off it, gliding slowly along `angle`."""
    tail = c.tail
    return f"""<g transform="translate({num(c.x)} {num(c.y)}) rotate({num(c.angle)})">
      <g class="comet">
        <path d="M0 -1.4 L{num(-tail)} -.25 L{num(-tail)} .25 L0 1.4Z" fill="url(#comet-tail)"/>
        <path d="M0 -.8 L{num(-tail * .75)} -4.2 L{num(-tail * .75)} -3 L0 .8Z" fill="url(#comet-ion)"/>
        <circle r="4.5" fill="url(#comet-glow)"/>
        <circle class="comet-head" r="1.3"/>
      </g>
    </g>"""


# ── Styles ───────────────────────────────────────────────────────────────────

NIGHT_VISITOR_STYLE = Template("""
    /* night: sky lanterns and a balloon take turns */
    .visitor          { opacity: 0; animation: none ${cycle}s linear var(--d) infinite; }
    .visitor.lanterns { animation-name: fly-lanterns; }
    .visitor.balloon  { animation-name: fly-balloon; }
    .lantern          { animation: lantern-sway 3.2s ease-in-out infinite alternate; }
    .lantern .paper   { fill: $paper; }
    .lantern .flame   { fill: $glow; }
    .lantern .halo    { animation: flicker 1.3s ease-in-out infinite alternate; }
    .balloon .envelope { fill: $ink; }
    .balloon .seams, .balloon .ropes { fill: none; stroke: $dark; stroke-width: .5; }
    .balloon .basket  { fill: $dark; }
    .balloon .flare   { animation: balloon-fire ${cycle}s linear var(--d) infinite; }
    .balloon .burner  { fill: $glow; animation: flicker .22s ease-in-out infinite alternate; }
    .balloon .drift   { animation: balloon-bob 4s ease-in-out infinite alternate; }
    .lift             { animation: balloon-lift ${cycle}s linear var(--d) infinite; }

    /* night: now and then a comet glides slowly across the upper sky */
    .comet            { opacity: 0; animation: comet ${comet_period}s linear ${comet_at}s infinite; }
    .comet-head       { fill: $snow; }

    $fly
    @keyframes lantern-sway { from { transform: rotate(-6deg); } to { transform: rotate(6deg); } }
    @keyframes flicker      { from { opacity: .6; } to { opacity: 1; } }
    @keyframes balloon-bob  { from { transform: translateY(-2px); } to { transform: translateY(2px); } }
    $comet
""")


def night_visitor_style(sky: Sky) -> str:
    cycle = sky.night_visit_cycle
    flights = [crossing(f"fly-{kind}", seconds, cycle)
               for kind, seconds in sky.night_flight.items() if kind != "balloon"]
    flights.append(balloon_flight(sky.night_flight["balloon"], cycle))
    return NIGHT_VISITOR_STYLE.substitute(
        cycle=num(cycle), dark=NIGHT_DARK, ink=NIGHT_INK, snow=SNOW,
        paper=LANTERN_PAPER, glow=LANTERN_GLOW, comet_period=num(sky.comet.period), comet_at=num(sky.comet.delay),
        fly="\n    ".join(flights), comet=comet_glide(sky.comet))


def balloon_flight(duration: float, cycle: float) -> str:
    """The balloon's flight as three keyframe sets. It drifts across at a steady pace,
    while it climbs slowly (easing off near the top) to var(--top), drifts there for
    BALLOON_HOVER of its flight, then sinks (gathering pace) to land var(--dy) down.
    It starts and ends hidden behind the ridge, so it only fades at the very ends.
    The fire burns bright on the climb, steady at the top, and dims on the way down."""
    top_from, top_to = duration * (1 - BALLOON_HOVER) / 2, duration * (1 + BALLOON_HOVER) / 2
    across = (f"@keyframes fly-balloon {{ 0% {{ opacity: 0; transform: none; }} {share(.5, cycle)}, "
              f"{share(duration - .5, cycle)} {{ opacity: 1; }} "
              f"{share(duration, cycle)}, 100% {{ opacity: 0; transform: translateX(var(--dx)); }} }}")
    up_and_down = (f"@keyframes balloon-lift {{ 0% {{ transform: none; animation-timing-function: cubic-bezier(.3, .2, .5, 1); }} "
                   f"{share(top_from, cycle)} {{ transform: translateY(var(--top)); animation-timing-function: linear; }} "
                   f"{share(top_to, cycle)} {{ transform: translateY(var(--top)); animation-timing-function: cubic-bezier(.5, 0, .7, .8); }} "
                   f"{share(duration, cycle)}, 100% {{ transform: translateY(var(--dy)); }} }}")
    fire = (f"@keyframes balloon-fire {{ 0%, {share(top_from, cycle)} {{ opacity: 1; }} "
            f"{share(top_to, cycle)} {{ opacity: .55; }} {share(duration, cycle)}, 100% {{ opacity: .2; }} }}")
    return "\n    ".join((across, up_and_down, fire))


def comet_glide(c: Comet) -> str:
    """Fades in, glides `travel` px, fades out, then waits out its period."""
    return (f"@keyframes comet {{ 0% {{ opacity: 0; transform: none; }} {share(1.5, c.period)}, "
            f"{share(c.flight - 2, c.period)} {{ opacity: 1; }} {share(c.flight, c.period)}, 100% "
            f"{{ opacity: 0; transform: translateX({num(c.travel)}px); }} }}")


# ── Glows ────────────────────────────────────────────────────────────────────

def night_glows() -> str:
    """Soft glows for the night visitors and the comet, as gradients rather than blurs."""
    radial = [("comet-glow", SNOW, ".7"), ("lantern-glow", LANTERN_GLOW, ".55"), ("balloon-flare", LANTERN_GLOW, ".75")]
    glows = "".join(f"""
    <radialGradient id="{gradient_id}">
      <stop offset="0" stop-color="{color}" stop-opacity="{peak}"/>
      <stop offset="1" stop-color="{color}" stop-opacity="0"/>
    </radialGradient>""" for gradient_id, color, peak in radial)
    tails = "".join(f"""
    <linearGradient id="{gradient_id}">
      <stop offset="0" stop-color="{color}" stop-opacity="0"/>
      <stop offset="1" stop-color="{color}" stop-opacity="{peak}"/>
    </linearGradient>""" for gradient_id, color, peak in (("comet-tail", SNOW, ".75"), ("comet-ion", COMET_ION, ".4")))
    return glows + tails
