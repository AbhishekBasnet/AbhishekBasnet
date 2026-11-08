"""The climber halfway up the devsecops peak: the figure, the footprint trail behind
them, and the gestures they make once stopped.

    climber(theme)          the figure, walking in and then standing
    footprints()            the trail over the peaks already climbed
    climber_style(theme)    the CSS: the walk, the muffler, and the gesture routine

Everything is drawn in the climber's own frame: feet at (0, 0), facing right, on a
slope of about 35°. Each moving part (legs, arms, head, muffler pieces) sits in a
group at its own hinge, so a plain CSS rotation swings it about that hinge.
"""

from __future__ import annotations

import math
from string import Template

from .config import (
    BINOCULARS, BOTTLE, CLIMBER_AT, CLIMBER_BINOCULARS_LEAD, CLIMBER_LOOK_TURN, CLIMBER_LOOKS,
    CLIMBER_RAISE, CLIMBER_STRIDE, CLIMBER_STRIDES, CLIMBER_X, FOOTPRINT_OFFSETS, FOOTPRINT_REVEAL,
    FOOTPRINT_SPACING, FOOTPRINT_SUMMIT_CLEAR, FOOTPRINT_TOE_OUT, HEADLAMP, MUFFLER, ORB, RIDGE, SUMMITS,
)
from .geometry import distance_to_polyline, height_on
from .keyframes import num, share
from .models import Gesture, Sky

Point = tuple[float, float]
Head = tuple[float, int]    # tilt in degrees (- looks up) and facing (1 ahead, -1 back)

WALK = CLIMBER_STRIDE * CLIMBER_STRIDES   # seconds from setting off to stopping


# ── Where the climber stands ─────────────────────────────────────────────────

def on_ridge(x: float) -> Point:
    """A spot for the climber's feet at x: on the ridge stroke, not sunk into it."""
    return x, height_on(RIDGE, x) - .6


def climber_spot() -> Point:
    """Where the climber stands once stopped."""
    return on_ridge(CLIMBER_X[1])


# ── The figure ───────────────────────────────────────────────────────────────

def climber(theme: str) -> str:
    """A small hiker with a big backpack, a beanie, a long muffler and a trekking
    pole. The outer group stands them where they stop; `.climber` walks them in from
    where they set off. The head carries the props (binoculars by day, a camera with
    its flash, a bottle) and, at night, the headlamp beam, so they all turn with it.
    A second arm hangs hidden along the torso until a gesture lifts it."""
    night = theme == "dark"
    start, stop = on_ridge(CLIMBER_X[0]), climber_spot()
    walk_in = f"--dx: {num(start[0] - stop[0])}px; --dy: {num(start[1] - stop[1])}px"
    beam = ("""
          <path class="beam" d="M4.3 -15 L24 -28.8 L27.5 -21.2 Z" fill="url(#beam)" filter="url(#spark)"/>"""
            if night else "")
    binoculars = ("" if night else """
          <g class="prop binoculars"><rect x="3.7" y="-16.4" width="2.8" height="1.1" rx=".35"/><rect x="3.9" y="-15.2" width="2.6" height="1" rx=".35"/></g>""")
    return f"""<g transform="translate({num(stop[0])} {num(stop[1])})">
    <g class="climber" style="{walk_in}">
      <g transform="translate(0 -7)"><g class="leg back">
        <path class="limb" d="M0 0 L-.9 4.1 L-1.8 8.3 L-.6 8.1"/>
      </g></g>
      <g transform="rotate(16 .8 -9.8)">
        <rect class="pack" x="-3.4" y="-12.8" width="3.2" height="5.6" rx="1"/>
        <rect class="bedroll" x="-3.7" y="-14.1" width="3.8" height="1.4" rx=".7"/>
      </g>
      <path class="limb torso" d="M0 -7 L1.6 -12.6"/>
      <g transform="translate(0 -7)"><g class="leg">
        <path class="limb" d="M0 0 L4 1.2 L2.6 5.2 L3.8 4.9"/>
      </g></g>
      <g transform="translate(2 -13.4)"><g class="turn"><g transform="translate(-2 13.4)">{beam}
          <circle class="head" cx="2.6" cy="-15.1" r="1.75"/>
          <path class="muffler" d="M.85 -15.4 A1.8 1.8 0 0 1 4.35 -15.4 Z"/>
          <circle class="muffler" cx="2.4" cy="-17.3" r=".6"/>
          <circle class="lamp" cx="4.2" cy="-15.1" r=".55"/>{binoculars}
          <g class="prop camera"><rect class="body" x="3.7" y="-16.5" width="2.6" height="1.8" rx=".35"/><circle class="lens" cx="6.4" cy="-15.6" r=".6"/></g>
          <g transform="translate(7.6 -15.6)"><g class="flash">
            <path class="spark" d="M0 -3 Q.4 -.4 3 0 Q.4 .4 0 3 Q-.4 .4 -3 0 Q-.4 -.4 0 -3Z"/><circle class="core" r=".8"/>
          </g></g>
          <rect class="prop bottle" x="0" y="-.65" width="3.4" height="1.3" rx=".5" transform="translate(4 -14.4) rotate(-28)"/>
      </g></g></g>
      <g transform="translate(.8 -13.2)"><g class="tail-a">
        <path class="muffler" d="M.4 -.6 L-4.6 -.8 L-4.6 .6 L.4 .6 Z"/>
        <g transform="translate(-4.6 -.1)"><g class="tail-b">
          <path class="muffler" d="M.4 -.7 L-4.6 -.7 L-4.6 .5 L.4 .6 Z"/>
          <g transform="translate(-4.6 -.1)"><g class="tail-c">
            <path class="muffler" d="M.4 -.6 L-4.4 -.55 L-3.7 0 L-4.5 .5 L.4 .6 Z"/>
          </g></g>
        </g></g>
      </g></g>
      <rect class="muffler" x=".6" y="-13.7" width="2.8" height="1.3" rx=".6" transform="rotate(16 2 -13)"/>
      <g transform="translate(1.6 -12.2)"><g class="gesture">
        <path class="limb" d="M0 0 L-1.15 4.04"/>
      </g></g>
      <g transform="translate(1.6 -12.2)"><g class="arm">
        <path class="limb" d="M0 0 L2 2.8"/>
        <path class="limb pole" d="M1.7 1.8 L5 8"/>
      </g></g>
    </g>
  </g>"""


# ── The footprint trail ──────────────────────────────────────────────────────

def footprints() -> str:
    """Prints every FOOTPRINT_SPACING px along the ridge, from its left end to just
    behind the climber's heels, left and right feet taking turns just above the
    line. Each print appears as the climber would have reached it: the stretch
    already climbed fills in as the ridge draws, the rest as the climber walks."""
    start_x, stop_x = CLIMBER_X
    last_x = stop_x - 4                      # just behind the heels
    prints, leftover, step = [], 0.0, 0
    for (ax, ay), (bx, by) in zip(RIDGE, RIDGE[1:]):
        length = math.hypot(bx - ax, by - ay)
        along_x, along_y = (bx - ax) / length, (by - ay) / length
        distance = leftover
        while distance <= length:
            x, y = ax + along_x * distance, ay + along_y * distance
            if x > last_x:
                return "\n    ".join(prints)
            lift = FOOTPRINT_OFFSETS[step % 2]                     # left foot, then right
            print_x, print_y = x + along_y * lift, y - along_x * lift   # lifted along the ridge's upward normal
            clear_of_summits = all(math.hypot(x - sx, y - sy) > FOOTPRINT_SUMMIT_CLEAR for sx, sy, _ in SUMMITS)
            off_the_line = distance_to_polyline((print_x, print_y), RIDGE) >= FOOTPRINT_OFFSETS[0] - .1
            if clear_of_summits and off_the_line:
                prints.append(footprint(print_x, print_y, along_x, along_y, step, appears_at(x)))
            step += 1
            distance += FOOTPRINT_SPACING
        leftover = distance - length
    return "\n    ".join(prints)


def appears_at(x: float) -> float:
    """Seconds after load the print at x appears."""
    start_x, stop_x = CLIMBER_X
    if x <= start_x:                         # already climbed: fills in as the ridge draws
        reveal_from, reveal_to = FOOTPRINT_REVEAL
        return reveal_from + (reveal_to - reveal_from) * (x - RIDGE[0][0]) / (start_x - RIDGE[0][0])
    return CLIMBER_AT + WALK * (x - start_x) / (stop_x - start_x)   # under the climber's feet as they walk


def footprint(x: float, y: float, along_x: float, along_y: float, step: int, appear: float) -> str:
    toe_out = FOOTPRINT_TOE_OUT * (1 if step % 2 else -1)   # toes turn out, away from the line between the feet
    angle = math.degrees(math.atan2(along_y, along_x)) + toe_out
    return (f'<ellipse class="print" cx="{num(x)}" cy="{num(y)}" rx="1.1" ry=".55" '
            f'transform="rotate({num(angle)} {num(x)} {num(y)})" style="--d: {num(appear)}s"/>')


# ── Gestures ─────────────────────────────────────────────────────────────────
# Each gesture is a list of poses over its duration. A pose sets any of the moving
# parts: the head (tilt and facing), the gesture arm (degrees turned from hanging
# along the torso), each prop's opacity, and the camera flash (opacity, scale).
# The routine's poses become one keyframe set per part, so the parts stay in step
# and only one gesture ever plays at a time.

NECK, SHOULDER, EYE = (2, -13.4), (1.6, -12.2), (3.6, -15.3)   # in the climber's frame
ARM_HANGING = 106                    # degrees: at rest the arm lies along the torso, hidden by it
HAND_AT_BROW = (3.8, -16.8)          # where the hand goes, in the head's frame
HAND_AT_EYES = (4.6, -14.9)          # holding the camera or binoculars
HAND_ON_BOTTLE = (5.4, -15.4)
REST_POSE = {"head": (0, 1), "arm": 0, "binoculars": 0, "camera": 0, "bottle": 0, "flash": (0, .3)}

Pose = dict[str, object]
Timeline = list[tuple[float, Pose]]   # (seconds into the gesture, pose)


def after_head_turn(p: Point, head: Head) -> Point:
    """Where a point drawn in the head's frame ends up once the head turns: the
    head's `rotate(tilt) scaleX(facing)` about the neck."""
    tilt, facing = head
    dx, dy, a = (p[0] - NECK[0]) * facing, p[1] - NECK[1], math.radians(tilt)
    return NECK[0] + dx * math.cos(a) - dy * math.sin(a), NECK[1] + dx * math.sin(a) + dy * math.cos(a)


def arm_reaching(hand: Point, head: Head) -> float:
    """The arm's turn from hanging that puts the hand on `hand`, a point in the head's
    frame. It always swings up over the front, never round the back."""
    x, y = after_head_turn(hand, head)
    angle = math.degrees(math.atan2(y - SHOULDER[1], x - SHOULDER[0]))
    return (angle - 360 if angle > ARM_HANGING else angle) - ARM_HANGING


def looking_at(target: Point, facing: int) -> Head:
    """The head turned to look at a point in the sky, facing ahead or back."""
    stand_x, stand_y = climber_spot()
    dx, dy = target[0] - (stand_x + EYE[0]), target[1] - (stand_y + EYE[1])
    if facing > 0:
        return max(-70.0, min(15.0, math.degrees(math.atan2(dy, dx)))), 1
    return max(20.0, min(70.0, math.degrees(math.atan2(-dy, -dx)))), -1   # at least 20° up, clear of the pack


def holding(head: Head, hand: Point, **props: float) -> Pose:
    """A pose with the hand on something at the face, the head turned as given."""
    return {"head": head, "arm": arm_reaching(hand, head), **props}


def shade_poses(duration: float, sky: Sky) -> Timeline:
    """A hand to the brow, gazing up at the sun, scanning a little."""
    up = looking_at(ORB, 1)
    scan = (up[0] + 8, 1)
    return [(CLIMBER_RAISE, holding(up, HAND_AT_BROW)), (duration / 2, holding(scan, HAND_AT_BROW)),
            (duration - CLIMBER_RAISE, holding(up, HAND_AT_BROW))]


def wave_poses(duration: float, sky: Sky) -> Timeline:
    """The arm up high, waving side to side four times."""
    head, high, low = (-6, 1), -60 - ARM_HANGING, -98 - ARM_HANGING
    raised = {"head": head, "arm": (high + low) / 2}
    waving = duration - 2 * CLIMBER_RAISE
    swings = [(CLIMBER_RAISE + waving * (n + 1) / 5, {"head": head, "arm": low if n % 2 == 0 else high})
              for n in range(4)]
    return [(CLIMBER_RAISE, raised), *swings, (duration - CLIMBER_RAISE, raised)]


def photo_poses(duration: float, sky: Sky) -> Timeline:
    """The camera to the eye, a flash halfway, the camera down."""
    head, click = (-8, 1), duration / 2
    aiming = holding(head, HAND_AT_EYES, camera=1)
    return [(CLIMBER_RAISE * .6, {"camera": 0}), (CLIMBER_RAISE, aiming),
            (click - .05, {"flash": (0, .3)}), (click + .06, {"flash": (1, 1.2)}), (click + .35, {"flash": (0, .6)}),
            (duration - CLIMBER_RAISE, aiming), (duration - CLIMBER_RAISE * .4, {"camera": 0})]


def drink_poses(duration: float, sky: Sky) -> Timeline:
    """The bottle to the lips, the head tipping back to drink, then down again."""
    sip = holding((-6, 1), HAND_ON_BOTTLE, bottle=1)
    gulp = holding((-36, 1), HAND_ON_BOTTLE, bottle=1)
    tip = .45                                  # seconds to tip the head back or forward
    return [(CLIMBER_RAISE * .6, {"bottle": 0}), (CLIMBER_RAISE, sip),
            (CLIMBER_RAISE + tip, gulp), (duration - CLIMBER_RAISE - tip, gulp),
            (duration - CLIMBER_RAISE, sip), (duration - CLIMBER_RAISE * .4, {"bottle": 0})]


def look_poses(duration: float, sky: Sky) -> Timeline:
    """Up, down and back over the shoulder; at night the beam follows."""
    turn = CLIMBER_LOOK_TURN
    hold = (duration - turn * (len(CLIMBER_LOOKS) + 1)) / len(CLIMBER_LOOKS)
    poses, elapsed = [], 0.0
    for head in CLIMBER_LOOKS:
        poses += [(elapsed + turn, {"head": head}), (elapsed + turn + hold, {"head": head})]
        elapsed += turn + hold
    return poses


def binocular_poses(duration: float, sky: Sky, ufo_index: int) -> Timeline:
    """Follow the UFO through binoculars, from where it parks to where it vanishes."""
    ufo, (rise, park, approach, whip) = sky.ufos[ufo_index], sky.ufo_times
    lead = CLIMBER_BINOCULARS_LEAD * rise
    whip_from, gone = rise + park + approach - lead, rise + park + approach + whip - lead
    parked, far = (ufo.x, ufo.y), (ufo.x + ufo.dx, ufo.y + ufo.dy)
    early_whip = (ufo.x + .3 * ufo.dx, ufo.y + .3 * ufo.dy)   # the whip starts slow: a third of the way at 60%
    facing = 1 if ufo.x >= climber_spot()[0] + EYE[0] else -1

    def watching(point: Point) -> Pose:
        return holding(looking_at(point, facing), HAND_AT_EYES, binoculars=1)

    return [(CLIMBER_RAISE * .6, {"binoculars": 0}), (CLIMBER_RAISE, watching(parked)), (whip_from, watching(parked)),
            (whip_from + .6 * whip, watching(early_whip)), (gone, watching(far)), (gone + .1, watching(far)),
            (duration - CLIMBER_RAISE * .4, {"binoculars": 0})]


GESTURE_POSES = {"shade": shade_poses, "wave": wave_poses, "photo": photo_poses,
                 "drink": drink_poses, "look": look_poses}


def gesture_poses(gesture: Gesture, sky: Sky) -> Timeline:
    """The poses of one gesture; it starts and ends at rest."""
    if gesture.kind == "binoculars":
        poses = binocular_poses(gesture.duration, sky, gesture.ufo)
    else:
        poses = GESTURE_POSES[gesture.kind](gesture.duration, sky)
    return [(0, REST_POSE), *poses, (gesture.duration, REST_POSE)]


def gesture_keyframes(sky: Sky, theme: str) -> str:
    """One keyframe set per moving part over the theme's routine."""
    routine = sky.routines[theme]
    tracks: dict[str, list[tuple[float, object]]] = {part: [] for part in REST_POSE}
    for gesture in routine.gestures:
        for seconds, pose in gesture_poses(gesture, sky):
            for part, value in pose.items():
                tracks[part].append((gesture.start + seconds, value))

    keyframe_sets = []
    for part, points in tracks.items():
        frames = [(0, REST_POSE[part]), *points, (routine.cycle, REST_POSE[part])]
        body = " ".join(f"{share(seconds, routine.cycle)} {{ {declaration(part, value)} }}" for seconds, value in frames)
        keyframe_sets.append(f"@keyframes climber-{part} {{ {body} }}")
    return "\n    ".join(keyframe_sets)


def declaration(part: str, value) -> str:
    """The CSS that puts one moving part into its pose."""
    if part == "head":
        tilt, facing = value
        return f"transform: rotate({num(tilt)}deg) scaleX({facing});"
    if part == "arm":
        return f"transform: rotate({num(value)}deg);"
    if part == "flash":
        opacity, scale = value
        return f"opacity: {num(opacity)}; transform: scale({num(scale)});"
    return f"opacity: {num(value)};"             # a prop showing or not


# ── Styles ───────────────────────────────────────────────────────────────────

CLIMBER_STYLE = Template("""
    /* the climber walks up to halfway and stops there; the muffler waves for good */
    .climber          { animation: climb ${climb}s linear ${at}s backwards; }
    .climber .leg,
    .climber .arm     { animation: stride ${stride}s ease-in-out ${at}s ${strides}; }
    .climber .back,
    .climber .arm     { animation-direction: reverse; }
    .climber .limb    { fill: none; stroke: var(--ink); stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round; }
    .climber .torso   { stroke-width: 2.6; }
    .climber .pole    { stroke-width: .6; }
    .climber .head    { fill: var(--ink); }
    .climber .pack    { fill: var(--accent); }
    .climber .bedroll { fill: var(--muted); }
    .climber .muffler { fill: $muffler; }
    .climber .lamp    { fill: $lamp; }
    .climber .tail-a  { animation: flutter-a .6s ease-in-out infinite alternate; }
    .climber .tail-b  { animation: flutter-b .6s ease-in-out -.2s infinite alternate; }
    .climber .tail-c  { animation: flutter-c .6s ease-in-out -.4s infinite alternate; }
    .climber .beam    { animation: beam 2.4s ease-in-out infinite alternate; }

    /* once stopped, one gesture at a time: every moving part runs the same loop */
    .climber .turn, .climber .gesture,
    .climber .prop, .climber .flash { animation: none ${routine_cycle}s ease-in-out ${routine_at}s infinite; }
    .climber .turn       { animation-name: climber-head; }
    .climber .gesture    { animation-name: climber-arm; }
    .climber .binoculars { animation-name: climber-binoculars; fill: $binoculars; }
    .climber .camera     { animation-name: climber-camera; }
    .climber .bottle     { animation-name: climber-bottle; fill: $bottle; }
    .climber .flash      { animation-name: climber-flash; }
    .climber .prop, .climber .flash { opacity: 0; }
    .climber .camera .body { fill: var(--muted); }
    .climber .camera .lens { fill: var(--accent); }
    .climber .flash .spark { fill: $lamp; }
    .climber .flash .core  { fill: #FFFFFF; }

    .print           { fill: var(--muted); opacity: .75; animation: print .4s ease-out var(--d) backwards; }

    @keyframes climb     { from { opacity: 0; transform: translate(var(--dx), var(--dy)); } 5% { opacity: 1; } to { transform: none; } }
    @keyframes stride    { 25% { transform: rotate(18deg); } 75% { transform: rotate(-18deg); } }
    @keyframes flutter-a { from { transform: rotate(-6deg); } to { transform: rotate(8deg); } }
    @keyframes flutter-b { from { transform: rotate(-12deg); } to { transform: rotate(12deg); } }
    @keyframes flutter-c { from { transform: rotate(-18deg); } to { transform: rotate(16deg); } }
    @keyframes beam      { from { opacity: .7; } to { opacity: 1; } }
    @keyframes print     { from { opacity: 0; } }
    $gestures
""")


def climber_style(theme: str, sky: Sky) -> str:
    routine = sky.routines[theme]
    return CLIMBER_STYLE.substitute(
        climb=num(WALK), at=num(CLIMBER_AT), stride=num(CLIMBER_STRIDE),
        strides=CLIMBER_STRIDES, muffler=MUFFLER, lamp=HEADLAMP, binoculars=BINOCULARS, bottle=BOTTLE,
        routine_cycle=num(routine.cycle), routine_at=num(routine.at), gestures=gesture_keyframes(sky, theme))
