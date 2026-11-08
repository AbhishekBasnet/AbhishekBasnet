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
from .geometry import (Box, contains, distance, distance_to_box, height_on, inside, overlaps,
                       segment_clear_of, segment_touches)
from .models import Cloud, Comet, Gesture, Meteor, Moon, Ribbon, Route, Routine, Satellite, Sky, Star, Ufo, Visit


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
    routines = {"light": day_routine(rng, ufos, ufo_times, ufo_cycle), "dark": night_routine(rng)}
    aurora = shape_aurora(rng)
    night_flight, night_visits, night_visit_cycle = plan_night_visits(rng)
    return Sky(clouds=clouds, cloudy_sun=cloudy_sun, wind=wind,
               visits=visits, flight=flight, visit_cycle=visit_cycle,
               stars=stars, meteors=meteors, moon=moon_on(day),
               aurora=aurora, satellites=satellites,
               satellite_pass=satellite_duration, satellite_cycle=satellite_cycle,
               ufos=ufos, ufo_times=ufo_times, ufo_cycle=ufo_cycle, routines=routines,
               night_visits=night_visits, night_flight=night_flight, night_visit_cycle=night_visit_cycle,
               comet=place_comet(rng))


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
    """The whole streak stays inside the sky, clear of the moon and of the text."""
    dx, dy = math.cos(math.radians(m.angle)), math.sin(math.radians(m.angle))
    tail = (m.x - m.length * dx, m.y - m.length * dy)
    end = (m.x + m.travel * dx, m.y + m.travel * dy)
    return (contains(cfg.METEOR_AREA, tail) and contains(cfg.METEOR_AREA, end)
            and segment_clear_of(tail, end, cfg.ORB, cfg.METEOR_MOON_CLEAR)
            and not any(segment_touches(tail, end, k) for k in cfg.KEEP_CLEAR))


def place_meteors(rng: random.Random) -> list[Meteor]:
    """Each meteor repeats on its own period, so together they never fall into a
    rhythm a viewer would notice; its streak lasts the same whatever the period."""
    found: list[Meteor] = []
    while len(found) < cfg.METEOR_COUNT:
        # alternate to the right and to the left, always downwards
        angle = rng.uniform(18, 38) if len(found) % 2 == 0 else rng.uniform(142, 162)
        m = Meteor(x=rng.uniform(70, 830), y=rng.uniform(62, 104), angle=angle,
                   length=rng.uniform(36, 84), width=rng.uniform(.8, 1.4), travel=rng.uniform(60, 120),
                   period=rng.uniform(*cfg.METEOR_PERIOD), flight=rng.uniform(*cfg.METEOR_FLIGHT), delay=0)
        if meteor_fits(m):
            found.append(m)
    # the first falls soon after the sky appears, the rest start within the window
    delays = [cfg.METEOR_FIRST] + sorted(rng.uniform(*cfg.METEOR_SPREAD) for _ in found[1:])
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
    """Two soft curtains low over the ridge. Their stretch of sky and folds are
    rolled daily; the upper edge runs a wave past the stretch each side, so the
    curtain fades out at its ends before the shape does."""
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
        ribbons.append(Ribbon(top=top, span=(left, left + width), thickness=rng.uniform(34, 52),
                              color=color, opacity=rng.uniform(*cfg.AURORA_OPACITY),
                              wave=wave))
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
    """Clear of the ridge below, the summit leader lines beside and the climber."""
    left, right = cfg.CLIMBER_X
    return (height_on(cfg.RIDGE, x) - y >= cfg.UFO_ABOVE_RIDGE
            and all(abs(x - sx) >= cfg.UFO_CLEAR_OF_LEADERS for sx, _, _ in cfg.SUMMITS)
            and not left - cfg.UFO_CLEAR_OF_CLIMBER <= x <= right + cfg.UFO_CLEAR_OF_CLIMBER)


def plan_ufos(rng: random.Random) -> tuple[list[Ufo], tuple[float, float, float, float], float]:
    """The day's UFOs taking turns, a random mix of ridge and sky arrivals. Returns
    them, the seconds to arrive, park, approach and whip off, and the full cycle."""
    times = (rng.uniform(*cfg.UFO_RISE), rng.uniform(*cfg.UFO_PARK),
             rng.uniform(*cfg.UFO_APPROACH), rng.uniform(*cfg.UFO_WHIP))
    from_sky = rng.randint(1, cfg.UFOS - 1)
    arrivals = [True] * from_sky + [False] * (cfg.UFOS - from_sky)
    rng.shuffle(arrivals)
    ufos, t = [], rng.uniform(*cfg.UFO_FIRST)
    first = t
    for sky_arrival in arrivals:
        ufos.append(ufo(rng, start=t, from_sky=sky_arrival))
        t += sum(times) + rng.uniform(*cfg.UFO_GAP)
    return ufos, times, t - first


def far_point(rng: random.Random) -> tuple[float, float]:
    left, top, right, bottom = cfg.UFO_FAR_AREA
    return rng.uniform(left, right), rng.uniform(top, bottom)


def ufo(rng: random.Random, start: float, from_sky: bool, attempts: int = 10_000) -> Ufo:
    """A parking spot over the ridge, a far point to vanish at and, for a sky
    arrival, another far point to appear at."""
    for _ in range(attempts):
        x, y = rng.uniform(cfg.LEFT + 30, cfg.RIGHT - 30), rng.uniform(*cfg.UFO_PARK_Y)
        exit_, entry = far_point(rng), far_point(rng)
        if not ufo_parks_well(x, y) or distance((x, y), exit_) < cfg.UFO_WHIP_MIN:
            continue
        if from_sky and (distance((x, y), entry) < cfg.UFO_WHIP_MIN or distance(entry, exit_) < cfg.UFO_PATHS_APART):
            continue
        # a ridge arrival starts far enough down to be fully hidden behind the ridge
        return Ufo(x=x, y=y, rise=height_on(cfg.RIDGE, x) - y + 16, dx=exit_[0] - x, dy=exit_[1] - y,
                   start=start, arrive=(entry[0] - x, entry[1] - y) if from_sky else None)
    raise RuntimeError("no UFO parking spot fits the rules in config")


# ── Climber's gestures ───────────────────────────────────────────────────────

def day_routine(rng: random.Random, ufos: list[Ufo], ufo_times: tuple[float, float, float, float],
                ufo_cycle: float) -> Routine:
    """Binoculars on every UFO, in step with the UFO loop, and the other day gestures
    in the gaps between: each only where it fits whole, with a rest either side."""
    rise, visit = ufo_times[0], sum(ufo_times)
    lead = cfg.CLIMBER_BINOCULARS_LEAD * rise
    first = ufos[0].start
    windows = [Gesture("binoculars", u.start - first + lead, visit - lead + .1 + cfg.CLIMBER_RAISE, ufo=i)
               for i, u in enumerate(ufos)]
    gaps = [(w.start + w.duration, nxt.start) for w, nxt in zip(windows, windows[1:])]
    gaps.append((windows[-1].start + windows[-1].duration, ufo_cycle))
    return Routine(fill_gaps(rng, cfg.CLIMBER_DAY, gaps, windows), ufo_cycle, first)


def night_routine(rng: random.Random) -> Routine:
    """The night gestures taking turns in a shuffled loop, from just after the climber stops."""
    order = list(cfg.CLIMBER_NIGHT)
    rng.shuffle(order)
    gestures, at = [], 0.0
    for kind in order:
        gestures.append(Gesture(kind, at, cfg.CLIMBER_GESTURES[kind]))
        at += cfg.CLIMBER_GESTURES[kind] + rng.uniform(*cfg.CLIMBER_REST)
    stopped = cfg.CLIMBER_AT + cfg.CLIMBER_STRIDE * cfg.CLIMBER_STRIDES
    return Routine(gestures, cycle=at, at=stopped + cfg.CLIMBER_REST[0])


def fill_gaps(rng: random.Random, kinds: tuple[str, ...], gaps: list[tuple[float, float]],
              fixed: list[Gesture]) -> list[Gesture]:
    """Takes `kinds` in a shuffled turn and places each in the gaps, wherever it fits
    whole between rests; returns them merged with the `fixed` gestures, in order."""
    order = list(kinds)
    rng.shuffle(order)
    placed, turn = [], 0
    for gap_start, gap_end in gaps:
        at = gap_start + rng.uniform(*cfg.CLIMBER_REST)
        while at + cfg.CLIMBER_GESTURES[order[turn % len(order)]] + cfg.CLIMBER_REST[0] <= gap_end:
            kind = order[turn % len(order)]
            placed.append(Gesture(kind, at, cfg.CLIMBER_GESTURES[kind]))
            at += cfg.CLIMBER_GESTURES[kind] + rng.uniform(*cfg.CLIMBER_REST)
            turn += 1
    return sorted(fixed + placed, key=lambda gesture: gesture.start)


# ── Day visitors ─────────────────────────────────────────────────────────────

def plan_visits(rng: random.Random) -> tuple[dict[str, float], list[Visit], float]:
    """A schedule where birds, the parachute, the paraglider and the plane take turns.

    Each visitor crosses, then the sky stays empty for VISIT_GAP seconds before the
    next. The parachute, paraglider and plane work through their day's routes in turn;
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
    low, high = cfg.VISIT_Y[kind]
    height = rng.uniform(low + cfg.ROUTE_JITTER, high - cfg.ROUTE_JITTER)
    heights = [height + rng.uniform(-cfg.ROUTE_JITTER, cfg.ROUTE_JITTER) for _ in range(cfg.ROUTES)]
    if kind in cfg.LANDINGS:
        return landing_routes(rng, kind, heights)
    span = cfg.OFFSTAGE[1] - cfg.OFFSTAGE[0]
    return [Route(edge(d), y, d * span, rng.uniform(*cfg.SINK[kind])) for d, y in zip(mixed_directions(rng), heights)]


def mixed_directions(rng: random.Random) -> list[int]:
    """ROUTES directions, 1 rightwards and -1 leftwards, with at least one of each."""
    lefts = rng.randint(1, cfg.ROUTES - 1)
    directions = [-1] * lefts + [1] * (cfg.ROUTES - lefts)
    rng.shuffle(directions)
    return directions


def edge(direction: int) -> float:
    """Where something flying in that direction enters, just off the edge."""
    return cfg.OFFSTAGE[0] if direction > 0 else cfg.OFFSTAGE[1]


def landing_routes(rng: random.Random, kind: str, heights: list[float], attempts: int = 10_000) -> list[Route]:
    """Landing spots spread over the kind's stretch of ridge. Each comes in from a
    side far enough away to come down gently, until the ridge hides it."""
    rules = cfg.LANDINGS[kind]
    for _ in range(attempts):
        spots = sorted(rng.uniform(*rules["area"]) for _ in heights)
        if any(b - a < rules["spacing"] for a, b in zip(spots, spots[1:])):
            continue
        directions = [d if abs(x - edge(d)) >= cfg.LANDING_MIN_DRIFT else -d
                      for x, d in zip(spots, mixed_directions(rng))]
        if set(directions) != {1, -1}:
            continue
        routes = [Route(edge(d), y, x - edge(d), height_on(cfg.RIDGE, x) + rules["depth"] - y)
                  for x, d, y in zip(spots, directions, heights)]
        rng.shuffle(routes)
        return routes
    raise RuntimeError(f"no set of {kind} landings fits the rules in config")


def bird_route(rng: random.Random) -> Route:
    direction = rng.choice((1, -1))
    return Route(edge(direction), rng.uniform(*cfg.VISIT_Y["birds"]),
                 direction * (cfg.OFFSTAGE[1] - cfg.OFFSTAGE[0]), rng.uniform(*cfg.SINK["birds"]))


def flock(rng: random.Random) -> tuple[tuple[float, float, float], ...]:
    """A loose V: the leader in front, the rest trailing and alternating sides."""
    return tuple((-i * rng.uniform(9, 14), (1 if i % 2 else -1) * i * rng.uniform(3, 6) if i else 0,
                  rng.uniform(.8, 1.1)) for i in range(rng.randint(*cfg.FLOCK_SIZE)))


# ── Night visitors ───────────────────────────────────────────────────────────

def plan_night_visits(rng: random.Random) -> tuple[dict[str, float], list[Visit], float]:
    """The night's schedule, on the day visitors' rules: one in the sky at a time,
    VISIT_GAP seconds of empty sky after each, no kind following itself (across the
    loop too), and every kind at least once. Each crossing takes a fresh path."""
    flight = {kind: rng.uniform(*seconds) for kind, seconds in cfg.NIGHT_FLIGHT.items()}
    kinds = list(cfg.NIGHT_FLIGHT)
    visits: list[Visit] = []
    at = 0.0
    while (at < cfg.VISIT_SCHEDULE or set(kinds) - {visit.kind for visit in visits}
           or visits[-1].kind == visits[0].kind):
        kind = rng.choice([other for other in kinds if not visits or other != visits[-1].kind])
        visits.append(night_visit(rng, kind, at))
        at += flight[kind] + rng.uniform(*cfg.VISIT_GAP)
    return flight, visits, at


def night_visit(rng: random.Random, kind: str, start: float) -> Visit:
    """One night visit: lanterns rise, or the balloon hops, from behind the ridge."""
    if kind == "lanterns":
        spread, below = cfg.LANTERN_SPREAD
        return Visit(kind, lantern_route(rng), start, flock=tuple(
            (rng.uniform(-spread, spread), rng.uniform(0, below), rng.uniform(.8, 1.1))
            for _ in range(rng.randint(*cfg.LANTERNS))))
    route, top = balloon_route(rng)
    return Visit(kind, route, start, top=top)


def hidden_below_ridge(x: float, half_width: float, above: float) -> float:
    """The highest y at x where something reaching `half_width` px either side and
    `above` px up from it is still wholly behind the ridge."""
    reach = int(half_width)
    return max(height_on(cfg.RIDGE, x + o) for o in range(-reach, reach + 1, 2)) + above


def lantern_route(rng: random.Random) -> Route:
    """Up from fully behind the ridge (glow included; the lanterns spread either side
    and below the route), drifting a little sideways, to fade out high."""
    x = rng.uniform(*cfg.LANTERN_AREA)
    hidden = hidden_below_ridge(x, cfg.LANTERN_SPREAD[0] + 10, 11)
    top = rng.uniform(*cfg.LANTERN_TOP)
    return Route(x, hidden, rng.uniform(*cfg.LANTERN_DRIFT), top - hidden)


def balloon_route(rng: random.Random) -> tuple[Route, float]:
    """Lift-off and landing spots behind the ridge (envelope, flare and bob all
    hidden), a hop apart, and how high the basket climbs in between."""
    while True:
        lift_off_x = rng.uniform(*cfg.BALLOON_AREA)
        landing_x = lift_off_x + rng.uniform(*cfg.BALLOON_HOP) * rng.choice((1, -1))
        if cfg.BALLOON_AREA[0] <= landing_x <= cfg.BALLOON_AREA[1]:
            # hidden: the envelope reaches 12 px either side and, with its bob, 28 px up
            lift_off_y, landing_y = hidden_below_ridge(lift_off_x, 12, 28), hidden_below_ridge(landing_x, 12, 28)
            route = Route(lift_off_x, lift_off_y, landing_x - lift_off_x, landing_y - lift_off_y)
            return route, rng.uniform(*cfg.BALLOON_TOP)


def comet_fits(c: Comet) -> bool:
    """The whole comet, tail to where it ends, stays inside the sky, clear of the moon and the text."""
    dx, dy = math.cos(math.radians(c.angle)), math.sin(math.radians(c.angle))
    tail = (c.x - c.tail * dx, c.y - c.tail * dy)
    end = (c.x + c.travel * dx, c.y + c.travel * dy)
    return (contains(cfg.COMET_AREA, tail) and contains(cfg.COMET_AREA, end)
            and segment_clear_of(tail, end, cfg.ORB, cfg.COMET_MOON_CLEAR)
            and not any(segment_touches(tail, end, k) for k in cfg.KEEP_CLEAR))


def place_comet(rng: random.Random) -> Comet:
    while True:
        rightward = rng.random() < .5
        tilt = rng.uniform(4, 14)
        c = Comet(x=rng.uniform(80, 820), y=rng.uniform(60, 110), angle=tilt if rightward else 180 - tilt,
                  tail=rng.uniform(*cfg.COMET_TAIL), travel=rng.uniform(*cfg.COMET_TRAVEL),
                  flight=rng.uniform(*cfg.COMET_FLIGHT), period=rng.uniform(*cfg.COMET_PERIOD),
                  delay=rng.uniform(*cfg.COMET_FIRST))
        if comet_fits(c):
            return c
