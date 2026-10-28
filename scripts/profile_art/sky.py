"""Rolls the day's sky from a seed.

An SVG cannot draw random numbers while it plays, so the randomness is baked in
here: the same seed always gives the same sky, and the daily build passes the
date. Every placement is rejection-sampled against the rules in config. The moon
is not random: it shows the real phase for the day.
"""

from __future__ import annotations

import math
import random
from dataclasses import replace
from datetime import date, datetime, timezone

from . import config as cfg
from .geometry import Box, contains, distance, distance_to_box, inside, overlaps, segment_clear_of
from .models import Cloud, Meteor, Moon, Ribbon, Satellite, Sky, Star, Visit


def roll_sky(seed: str, day: date) -> Sky:
    rng = random.Random(seed)
    wind = rng.uniform(*cfg.WIND_PERIOD)
    clouds = place_clouds(rng, cfg.CLOUDS_MIN + (cfg.CLOUDS_EXTRA if rng.random() < .5 else 0))
    cloudy_sun = rng.random() < cfg.SUN_CLOUD_CHANCE
    if cloudy_sun:
        clouds.append(cfg.SUN_CLOUD)
    meteors = place_meteors(rng)
    stars = place_stars(rng)
    flight, visits, visit_cycle = plan_visits(rng)
    return Sky(clouds=clouds, cloudy_sun=cloudy_sun, wind=wind,
               visits=visits, flight=flight, visit_cycle=visit_cycle,
               stars=stars, meteors=meteors, moon=moon_on(day),
               aurora=shape_aurora(rng), satellite=plan_satellite(rng))


# ── Clouds ───────────────────────────────────────────────────────────────────

def sway(scale: float) -> float:
    """px a cloud sways either side of rest. Bigger clouds read as nearer, so they
    travel further in the shared wind and look faster."""
    return 30 * scale - 6


def cloud_box(c: Cloud) -> Box:
    """Area a cloud covers across its whole sway."""
    return c.x - c.reach, c.y - 27 * c.scale, c.x + 60 * c.scale + c.reach, c.y


def cloud_fits(c: Cloud, taken: list[Box]) -> bool:
    box = cloud_box(c)
    return (inside(box, cfg.CLOUD_AREA)
            and not any(overlaps(box, k) for k in cfg.KEEP_CLEAR)
            and not any(overlaps(box, t, cfg.CLOUD_GAP) for t in taken)
            and distance_to_box(cfg.ORB, box) > cfg.SUN_CLEAR)


def place_clouds(rng: random.Random, count: int) -> list[Cloud]:
    """Scatter clouds with no overlaps. The spot over the sun is always held for
    SUN_CLOUD, so the layout works whether or not that cloud appears."""
    left, top, right, base = cfg.CLOUD_AREA
    while True:
        taken, placed = [cloud_box(cfg.SUN_CLOUD)], []
        for i in range(count):
            for _ in range(400):
                k = rng.uniform(*(cfg.LEAD_CLOUD_SCALE if i == 0 else cfg.CLOUD_SCALE))
                c = Cloud(x=rng.uniform(left, right - 60 * k), y=rng.uniform(top + 27 * k, base),
                          scale=k, reach=sway(k))
                if cloud_fits(c, taken):
                    taken.append(cloud_box(c))
                    placed.append(c)
                    break
            else:
                break   # this layout boxed itself in; start again
        if len(placed) == count:
            return sorted(placed, key=lambda c: c.x)


# ── Shooting stars ───────────────────────────────────────────────────────────

def meteor_fits(m: Meteor) -> bool:
    """The whole streak stays inside the sky and clear of the moon."""
    dx, dy = math.cos(math.radians(m.angle)), math.sin(math.radians(m.angle))
    tail = (m.x - m.length * dx, m.y - m.length * dy)
    end = (m.x + m.travel * dx, m.y + m.travel * dy)
    return (contains(cfg.METEOR_AREA, tail) and contains(cfg.METEOR_AREA, end)
            and segment_clear_of(tail, end, cfg.ORB, cfg.METEOR_MOON_CLEAR))


def place_meteors(rng: random.Random) -> list[Meteor]:
    """Each meteor repeats on its own period, so together they never fall into a
    rhythm a viewer would notice."""
    found: list[Meteor] = []
    while len(found) < cfg.METEOR_COUNT:
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


# ── Stars ────────────────────────────────────────────────────────────────────

def star_fits(p: tuple[int, int], stars: list[Star]) -> bool:
    return (distance(p, cfg.ORB) >= cfg.MOON_CLEAR
            and not any(contains(k, p) for k in cfg.KEEP_CLEAR)
            and all(distance(p, (s.x, s.y)) >= cfg.STAR_SPACING for s in stars))


def place_stars(rng: random.Random) -> list[Star]:
    """Spaced-out random stars: mostly small and faint, a few brighter."""
    left, top, right, bottom = cfg.STAR_AREA
    count = rng.randint(*cfg.STAR_COUNT)
    while True:
        stars: list[Star] = []
        for _ in range(count * 60):
            p = round(rng.uniform(left, right)), round(rng.uniform(top, bottom))
            if not star_fits(p, stars):
                continue
            # the first is the bright one; the rest skew small, and brighter stars shine steadier
            size = 1.0 if not stars else rng.random() ** 2 * .75
            stars.append(Star(x=p[0], y=p[1], r=.9 + .9 * size, opacity=.5 + .5 * size,
                              period=rng.uniform(3, 5.4), delay=rng.uniform(4.6, 6.5)))
            if len(stars) == count:
                return stars


# ── Moon ─────────────────────────────────────────────────────────────────────

def moon_on(day: date) -> Moon:
    """The real phase on the evening of `day`, floored at a slim sliver."""
    evening = datetime.combine(day, cfg.MOON_VIEWING, tzinfo=timezone.utc)
    age = (evening - cfg.NEW_MOON_EPOCH).total_seconds() / 86400 % cfg.SYNODIC_MONTH
    phase = age / cfg.SYNODIC_MONTH
    lit = (1 - math.cos(2 * math.pi * phase)) / 2
    return Moon(phase=phase, lit=max(lit, cfg.MOON_MIN_LIT))


# ── Aurora ───────────────────────────────────────────────────────────────────

def shape_aurora(rng: random.Random) -> list[Ribbon]:
    """Two soft curtains low over the ridge; their stretch of sky and wavy upper
    edges are rolled daily."""
    ribbons = []
    for i, color in enumerate(cfg.AURORA_COLORS):
        base = rng.uniform(*cfg.AURORA_BASE_Y) - i * 22     # the second hangs higher
        width = rng.uniform(*cfg.AURORA_WIDTH)
        left = rng.uniform(cfg.LEFT, cfg.RIGHT - width)
        amp, waves, shift = rng.uniform(8, 20), rng.uniform(1.2, 2.4), rng.uniform(0, 2 * math.pi)
        span = cfg.RIGHT - cfg.LEFT
        top = [(x, base - amp * math.sin(2 * math.pi * waves * (x - cfg.LEFT) / span + shift))
               for x in range(cfg.LEFT - 60, cfg.RIGHT + 61, 40)]
        ribbons.append(Ribbon(top=top, span=(left, left + width), thickness=rng.uniform(34, 52),
                              color=color, opacity=rng.uniform(*cfg.AURORA_OPACITY),
                              sway=rng.uniform(14, 26), period=rng.uniform(18, 30)))
    return ribbons


# ── Satellite ────────────────────────────────────────────────────────────────

def plan_satellite(rng: random.Random) -> Satellite:
    """A steady dot crossing edge to edge, clear of the moon."""
    while True:
        rightward = rng.random() < .5
        tilt = rng.uniform(-6, 6)
        angle = tilt if rightward else 180 - tilt
        x = cfg.OFFSTAGE[0] if rightward else cfg.OFFSTAGE[1]
        y = rng.uniform(*cfg.SATELLITE_Y)
        travel = (cfg.OFFSTAGE[1] - cfg.OFFSTAGE[0]) / math.cos(math.radians(tilt))
        end = (x + travel * math.cos(math.radians(angle)), y + travel * math.sin(math.radians(angle)))
        if (cfg.SATELLITE_Y[0] - 10 <= end[1] <= cfg.SATELLITE_Y[1] + 10
                and segment_clear_of((x, y), end, cfg.ORB, cfg.SATELLITE_MOON_CLEAR)):
            duration = rng.uniform(*cfg.SATELLITE_PASS)
            return Satellite(x=x, y=y, angle=angle, travel=travel, duration=duration,
                             cycle=duration + rng.uniform(*cfg.SATELLITE_GAP), delay=rng.uniform(8, 20))


# ── Day visitors ─────────────────────────────────────────────────────────────

def plan_visits(rng: random.Random) -> tuple[dict[str, float], list[Visit], float]:
    """A schedule where birds, the paraglider and the plane take turns.

    Each visitor crosses edge to edge, then the sky stays empty for VISIT_GAP
    seconds before the next. No kind follows itself, including across the loop,
    and every kind appears at least once. Returns the day's crossing time per
    kind, the visits, and the schedule length.
    """
    flight = {kind: rng.uniform(*span) for kind, span in cfg.FLIGHT.items()}
    kinds = list(cfg.FLIGHT)
    visits: list[Visit] = []
    t = 0.0
    while (t < cfg.VISIT_SCHEDULE or {v.kind for v in visits} != set(kinds)
           or visits[-1].kind == visits[0].kind):
        kind = rng.choice([k for k in kinds if not visits or k != visits[-1].kind])
        visits.append(visit(rng, kind, start=t))
        t += flight[kind] + rng.uniform(*cfg.VISIT_GAP)
    return flight, visits, t


def visit(rng: random.Random, kind: str, start: float) -> Visit:
    rightward = rng.random() < .5
    x = cfg.OFFSTAGE[0] if rightward else cfg.OFFSTAGE[1]
    dx = (cfg.OFFSTAGE[1] - cfg.OFFSTAGE[0]) * (1 if rightward else -1)
    flock: tuple = ()
    if kind == "birds":
        # a loose V: the leader in front, the rest trailing and alternating sides
        size = rng.randint(*cfg.FLOCK_SIZE)
        flock = tuple((-i * rng.uniform(9, 14), (1 if i % 2 else -1) * i * rng.uniform(3, 6) if i else 0,
                       rng.uniform(.8, 1.1)) for i in range(size))
    return Visit(kind=kind, x=x, y=rng.uniform(*cfg.VISIT_Y[kind]), dx=dx,
                 dy=rng.uniform(*cfg.VISIT_DRIFT[kind]), start=start, flock=flock)
