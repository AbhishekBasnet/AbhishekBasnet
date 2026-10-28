"""Rolls the day's sky from a seed.

An SVG cannot draw random numbers while it plays, so the randomness is baked in
here: the same seed always gives the same sky, and the daily build passes the
date. Every placement is rejection-sampled against the rules in config.
"""

from __future__ import annotations

import math
import random
from dataclasses import replace

from . import config as cfg
from .geometry import Box, contains, distance, distance_to_box, inside, overlaps, segment_clear_of
from .models import Cloud, Meteor, Sky, Star


def roll_sky(seed: str) -> Sky:
    rng = random.Random(seed)
    wind = rng.uniform(*cfg.WIND_PERIOD)
    clouds = place_clouds(rng, cfg.CLOUDS_MIN + (cfg.CLOUDS_EXTRA if rng.random() < .5 else 0))
    cloudy_sun = rng.random() < cfg.SUN_CLOUD_CHANCE
    if cloudy_sun:
        clouds.append(cfg.SUN_CLOUD)
    meteors = place_meteors(rng)
    stars = place_stars(rng)
    return Sky(clouds=clouds, cloudy_sun=cloudy_sun, wind=wind, stars=stars, meteors=meteors)


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
