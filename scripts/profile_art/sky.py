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
from .geometry import Box, contains, distance, distance_to_box, height_on, inside, overlaps, segment_clear_of
from .models import Cloud, Meteor, Moon, Ribbon, Route, Satellite, Sky, Star, Ufo, Visit


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
    satellites, satellite_duration, satellite_cycle = plan_satellites(rng)
    ufos, ufo_times, ufo_cycle = plan_ufos(rng)
    return Sky(clouds=clouds, cloudy_sun=cloudy_sun, wind=wind,
               visits=visits, flight=flight, visit_cycle=visit_cycle,
               stars=stars, meteors=meteors, moon=moon_on(day),
               aurora=shape_aurora(rng), satellites=satellites,
               satellite_pass=satellite_duration, satellite_cycle=satellite_cycle,
               ufos=ufos, ufo_times=ufo_times, ufo_cycle=ufo_cycle)


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
    """Two soft curtains low over the ridge. Their stretch of sky, folds and flow
    are rolled daily; the upper edge repeats every wave so the folds can flow."""
    ribbons = []
    for i, color in enumerate(cfg.AURORA_COLORS):
        base = rng.uniform(*cfg.AURORA_BASE_Y) - i * 22     # the second hangs higher
        width = rng.uniform(*cfg.AURORA_WIDTH)
        left = rng.uniform(cfg.LEFT, cfg.RIGHT - width)
        wave = rng.uniform(*cfg.AURORA_WAVE)
        amp, ripple, shift = rng.uniform(8, 18), rng.uniform(2, 6), rng.uniform(0, 2 * math.pi)
        step = wave / 6
        xs = [left - wave + k * step for k in range(int((width + 2 * wave) / step) + 2)]
        top = [(x, base - amp * math.sin(2 * math.pi * x / wave + shift)
                     - ripple * math.sin(4 * math.pi * x / wave + 2 * shift)) for x in xs]
        flow = rng.uniform(*cfg.AURORA_FLOW) * rng.choice((1, -1))
        ribbons.append(Ribbon(top=top, span=(left, left + width), thickness=rng.uniform(34, 52),
                              color=color, opacity=rng.uniform(*cfg.AURORA_OPACITY),
                              wave=wave, flow=flow))
    return ribbons


# ── Satellite ────────────────────────────────────────────────────────────────

def satellite_path(s: Satellite, samples: int = 24) -> list[tuple[float, float]]:
    """Points along the pass: a straight line lifted by a parabola peaking mid-way."""
    return [(s.x + s.dx * t, s.y + s.dy * t - s.arc * 4 * t * (1 - t))
            for t in (i / samples for i in range(samples + 1))]


def satellite_fits(s: Satellite) -> bool:
    path = satellite_path(s)
    return (min(y for _, y in path) >= cfg.SATELLITE_TOP
            and all(distance(p, cfg.ORB) >= cfg.SATELLITE_MOON_CLEAR for p in path))


def plan_satellites(rng: random.Random) -> tuple[list[Satellite], float, float]:
    """The day's satellites taking turns: each its own arc and lean, with clear sky
    between passes. Returns the passes, the seconds per pass and the full cycle."""
    duration = rng.uniform(*cfg.SATELLITE_PASS)
    passes, t = [], rng.uniform(*cfg.SATELLITE_FIRST)
    first = t
    for _ in range(cfg.SATELLITES):
        passes.append(satellite_pass(rng, start=t))
        t += duration + rng.uniform(*cfg.SATELLITE_GAP)
    return passes, duration, t - first


def satellite_pass(rng: random.Random, start: float, attempts: int = 10_000) -> Satellite:
    for _ in range(attempts):
        rightward = rng.random() < .5
        y, end_y = rng.uniform(*cfg.SATELLITE_Y), rng.uniform(*cfg.SATELLITE_Y)
        s = Satellite(x=cfg.OFFSTAGE[0] if rightward else cfg.OFFSTAGE[1], y=y,
                      dx=(cfg.OFFSTAGE[1] - cfg.OFFSTAGE[0]) * (1 if rightward else -1), dy=end_y - y,
                      arc=rng.uniform(*cfg.SATELLITE_ARC), lean=rng.uniform(-cfg.SATELLITE_LEAN, cfg.SATELLITE_LEAN),
                      start=start)
        if satellite_fits(s):
            return s
    raise RuntimeError("no satellite path fits the rules in config")


# ── UFOs ─────────────────────────────────────────────────────────────────────

def ufo_parks_well(x: float, y: float) -> bool:
    """Clear of the ridge below and the summit leader lines beside."""
    return (height_on(cfg.RIDGE, x) - y >= cfg.UFO_ABOVE_RIDGE
            and all(abs(x - sx) >= cfg.UFO_CLEAR_OF_LEADERS for sx, _, _ in cfg.SUMMITS))


def plan_ufos(rng: random.Random) -> tuple[list[Ufo], tuple[float, float, float], float]:
    """The night's UFOs taking turns. Returns them, the seconds to rise, park and
    leave, and the full cycle."""
    times = (rng.uniform(*cfg.UFO_RISE), rng.uniform(*cfg.UFO_PARK), rng.uniform(*cfg.UFO_LEAVE))
    ufos, t = [], rng.uniform(*cfg.UFO_FIRST)
    first = t
    for _ in range(cfg.UFOS):
        ufos.append(ufo(rng, start=t))
        t += sum(times) + rng.uniform(*cfg.UFO_GAP)
    return ufos, times, t - first


def ufo(rng: random.Random, start: float, attempts: int = 10_000) -> Ufo:
    for _ in range(attempts):
        x, y = rng.uniform(cfg.LEFT + 30, cfg.RIGHT - 30), rng.uniform(*cfg.UFO_PARK_Y)
        if ufo_parks_well(x, y):
            angle = math.radians(rng.uniform(*cfg.UFO_LEAVE_ANGLE))
            distance_ = rng.uniform(*cfg.UFO_LEAVE_DISTANCE)
            # start far enough down that it is fully hidden behind the ridge
            return Ufo(x=x, y=y, rise=height_on(cfg.RIDGE, x) - y + 16,
                       dx=distance_ * math.cos(angle), dy=distance_ * math.sin(angle), start=start)
    raise RuntimeError("no UFO parking spot fits the rules in config")


# ── Day visitors ─────────────────────────────────────────────────────────────

def plan_visits(rng: random.Random) -> tuple[dict[str, float], list[Visit], float]:
    """A schedule where birds, the parachute, the hang glider and the plane take turns.

    Each visitor crosses, then the sky stays empty for VISIT_GAP seconds before the
    next. The parachute, glider and plane work through their day's routes in turn;
    birds take a fresh path every time. No kind follows itself, including across
    the loop, and the schedule runs until every route has been flown. Returns the
    day's crossing time per kind, the visits, and the schedule length.
    """
    flight = {kind: rng.uniform(*span) for kind, span in cfg.FLIGHT.items()}
    routes = {kind: daily_routes(rng, kind) for kind in cfg.ROUTE_KINDS}
    flown = {kind: 0 for kind in cfg.ROUTE_KINDS}
    kinds = list(cfg.FLIGHT)
    visits: list[Visit] = []
    t = 0.0
    while (t < cfg.VISIT_SCHEDULE or any(n < cfg.ROUTES for n in flown.values())
           or "birds" not in {v.kind for v in visits} or visits[-1].kind == visits[0].kind):
        kind = rng.choice([k for k in kinds if not visits or k != visits[-1].kind])
        if kind == "birds":
            visits.append(Visit(kind, bird_route(rng), start=t, flock=flock(rng)))
        else:
            visits.append(Visit(kind, routes[kind][flown[kind] % cfg.ROUTES], start=t))
            flown[kind] += 1
        t += flight[kind] + rng.uniform(*cfg.VISIT_GAP)
    return flight, visits, t


def daily_routes(rng: random.Random, kind: str) -> list[Route]:
    """ROUTES paths for the day: a random mix of directions (at least one each way),
    each a little above or below the day's height for this kind."""
    lefts = rng.randint(1, cfg.ROUTES - 1)
    directions = [-1] * lefts + [1] * (cfg.ROUTES - lefts)
    rng.shuffle(directions)
    low, high = cfg.VISIT_Y[kind]
    height = rng.uniform(low + cfg.ROUTE_JITTER, high - cfg.ROUTE_JITTER)
    return [route(rng, kind, d, height + rng.uniform(-cfg.ROUTE_JITTER, cfg.ROUTE_JITTER)) for d in directions]


def route(rng: random.Random, kind: str, direction: int, y: float) -> Route:
    x = cfg.OFFSTAGE[0] if direction > 0 else cfg.OFFSTAGE[1]
    if kind == "parachute":
        # drifts in on the wind while it comes down, until the ridge hides it
        return Route(x, y, direction * rng.uniform(*cfg.PARACHUTE_DRIFT), cfg.PARACHUTE_LANDING_Y - y)
    return Route(x, y, direction * (cfg.OFFSTAGE[1] - cfg.OFFSTAGE[0]), rng.uniform(*cfg.SINK[kind]))


def bird_route(rng: random.Random) -> Route:
    return route(rng, "birds", rng.choice((1, -1)), rng.uniform(*cfg.VISIT_Y["birds"]))


def flock(rng: random.Random) -> tuple[tuple[float, float, float], ...]:
    """A loose V: the leader in front, the rest trailing and alternating sides."""
    return tuple((-i * rng.uniform(9, 14), (1 if i % 2 else -1) * i * rng.uniform(3, 6) if i else 0,
                  rng.uniform(.8, 1.1)) for i in range(rng.randint(*cfg.FLOCK_SIZE)))
