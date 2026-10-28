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
    flight: float     # seconds the streak lasts
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
    """One curtain of the aurora. Its upper edge repeats every `wave` px, so the
    folds can flow sideways forever while the lit stretch of sky stays put."""
    top: list[tuple[float, float]]   # points along its upper edge, a wave beyond the span each side
    span: tuple[float, float]        # left and right of the stretch of sky it lights; fades at both ends
    thickness: float
    color: str
    opacity: float
    wave: float       # px from one fold to the next
    flow: float       # seconds for the folds to move one wave along; negative flows left


@dataclass(frozen=True)
class Satellite:
    """One pass: edge to edge on a gentle arc, as real satellites appear to."""
    x: float          # start, just off one edge
    y: float
    dx: float         # px to the far edge; negative flies leftwards
    dy: float         # px lower (+) or higher (-) the far end is
    arc: float        # px the middle of the pass rises above the straight line
    lean: float       # degrees the whole craft is turned from level
    start: float      # seconds after load of its first pass


@dataclass(frozen=True)
class Route:
    """A path across the sky: in from just off one edge, then dx across and dy down."""
    x: float
    y: float
    dx: float         # negative flies leftwards
    dy: float         # positive sinks, negative climbs


@dataclass(frozen=True)
class Visit:
    """One crossing by a bird flock, the parachute, the paraglider or the plane."""
    kind: str         # "birds", "parachute", "paraglider" or "plane"
    route: Route
    start: float      # seconds into the schedule
    flock: tuple[tuple[float, float, float], ...] = ()   # birds only: offset x, offset y, size


@dataclass(frozen=True)
class Ufo:
    """Arrives to park at (x, y), comes closer, then whips off to vanish (dx, dy) away.
    It either rises `rise` px from behind the ridge or, when `arrive` is set, swoops
    in from that offset in the far sky."""
    x: float
    y: float
    rise: float
    dx: float
    dy: float
    start: float      # seconds after load of its first visit
    arrive: tuple[float, float] | None = None


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
    satellites: list[Satellite]   # night: take turns, one per pass
    satellite_pass: float         # night: seconds each pass takes
    satellite_cycle: float        # night: seconds before the first comes round again
    ufos: list[Ufo]               # day and night: take turns
    ufo_times: tuple[float, float, float, float]   # seconds to rise, park, approach and whip off
    ufo_cycle: float              # night: seconds before the first comes round again
