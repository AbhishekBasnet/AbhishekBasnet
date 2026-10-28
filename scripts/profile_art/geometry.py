"""Small geometry helpers. A Box is (left, top, right, bottom)."""

from __future__ import annotations

import math

Box = tuple[float, float, float, float]
Point = tuple[float, float]


def inside(box: Box, area: Box) -> bool:
    return box[0] >= area[0] and box[1] >= area[1] and box[2] <= area[2] and box[3] <= area[3]


def contains(area: Box, p: Point) -> bool:
    return area[0] <= p[0] <= area[2] and area[1] <= p[1] <= area[3]


def overlaps(a: Box, b: Box, gap: float = 0) -> bool:
    return a[0] < b[2] + gap and b[0] < a[2] + gap and a[1] < b[3] + gap and b[1] < a[3] + gap


def distance(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def distance_to_box(p: Point, box: Box) -> float:
    nearest = (min(max(p[0], box[0]), box[2]), min(max(p[1], box[1]), box[3]))
    return distance(p, nearest)


def segment_clear_of(start: Point, end: Point, centre: Point, radius: float, samples: int = 20) -> bool:
    """True if no sampled point of the segment comes within radius of centre."""
    return all(
        distance((start[0] + (end[0] - start[0]) * i / samples, start[1] + (end[1] - start[1]) * i / samples), centre) >= radius
        for i in range(samples + 1))
