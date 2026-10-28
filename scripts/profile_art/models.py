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
class Moon:
    phase: float      # 0 new → .5 full → 1 new again
    lit: float        # fraction of the disc that is lit, never below the slim-sliver floor

    @property
    def waxing(self) -> bool:
        return self.phase < .5


@dataclass(frozen=True)
class Ribbon:
    """One curtain of the aurora."""
    top: list[tuple[float, float]]   # points along its upper edge
    span: tuple[float, float]        # left and right of the stretch of sky it lights; fades at both ends
    thickness: float
    color: str
    opacity: float
    sway: float       # px it drifts either side of rest
    period: float     # seconds per drift


@dataclass(frozen=True)
class Satellite:
    x: float          # start, just off one edge
    y: float
    angle: float      # direction of travel, degrees clockwise from east
    travel: float     # px to the far edge
    duration: float   # seconds to cross
    cycle: float      # seconds from one pass to the next
    delay: float      # first pass, seconds after load


@dataclass(frozen=True)
class Visit:
    """One crossing by a bird flock, the paraglider or the plane."""
    kind: str         # "birds", "paraglider" or "plane"
    x: float          # start, just off one edge
    y: float
    dx: float         # px to the far edge; negative flies leftwards
    dy: float         # px it rises (negative) or sinks on the way
    start: float      # seconds into the schedule
    flock: tuple[tuple[float, float, float], ...] = ()   # birds only: offset x, offset y, size


@dataclass(frozen=True)
class Sky:
    """Everything that changes from day to day."""
    clouds: list[Cloud]
    cloudy_sun: bool
    wind: float              # seconds per crossing
    visits: list[Visit]      # day: one visitor at a time
    flight: dict[str, float] # day: seconds each kind takes to cross
    visit_cycle: float       # day: seconds before the schedule repeats
    stars: list[Star]        # night: brightest first
    meteors: list[Meteor]
    moon: Moon
    aurora: list[Ribbon]
    satellite: Satellite
