"""Plain data types shared by the sky generator and the renderer."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Cloud:
    x: float          # left edge at rest
    y: float          # flat base
    scale: float      # 1 = the largest cloud
    reach: float      # px it sways either side of rest


@dataclass(frozen=True)
class Star:
    x: float
    y: float
    r: float
    opacity: float
    period: float     # seconds for one twinkle
    delay: float


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


@dataclass(frozen=True)
class Sky:
    """Everything that changes from day to day."""
    clouds: list[Cloud]
    cloudy_sun: bool
    wind: float              # seconds per crossing
    stars: list[Star]        # brightest first
    meteors: list[Meteor]
