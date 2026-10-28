"""Every tunable value in one place. Coordinates are SVG user units."""

from datetime import datetime, time, timezone

from .models import Cloud

# ── Canvas ───────────────────────────────────────────────────────────────────

VIEW_X, VIEW_Y, WIDTH, HEIGHT = 46, 36, 808, 370
LEFT, RIGHT = 48, 852

SANS = "'Helvetica Neue', Helvetica, 'Segoe UI', Arial, sans-serif"
MONO = "ui-monospace, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

# ── Palette (Nord) ───────────────────────────────────────────────────────────

THEMES = {
    "light": dict(ink="#2E3440", muted="#6B7891", accent="#5E81AC", rule="#D8DEE9",
                  orb="#BF616A", glow="#D08770", ripple="#BF616A"),
    "dark": dict(ink="#ECEFF4", muted="#8F9BB3", accent="#88C0D0", rule="#3B4252",
                 orb="#E5E9F0", glow="#E5E9F0", ripple="#D8DEE9"),
}
SNOW = "#ECEFF4"
CLOUD_FILL = "#E5E9F0"

# ── Text ─────────────────────────────────────────────────────────────────────

NAME = "Abhishek Man Basnet"
ROLE = "backend engineer · nepal"
COORDS = "28.39° N   84.12° E"  # geographic centre of Nepal
TITLE = f"{NAME}, backend engineer — flutter, go, fastapi"

LEGEND = [
    ("go", "services · concurrency · systems"),
    ("fastapi", "python apis"),
    ("flutter", "the clients on top"),
]

# ── Landscape ────────────────────────────────────────────────────────────────

RIDGE = [
    (48, 332), (110, 322), (150, 326), (210, 292), (236, 300), (268, 264), (300, 284),
    (338, 272), (380, 296), (420, 254), (452, 220), (486, 246), (516, 238), (560, 284),
    (604, 272), (652, 250), (690, 282), (740, 306), (790, 298), (852, 320),
]
SUMMITS = [(268, 264, "flutter"), (452, 220, "go"), (652, 250, "fastapi")]
LABEL_Y = 170
GROUND_Y = 342
ORB = (792, 92)                      # the sun by day, the moon by night
KEEP_CLEAR = [(40, 40, 224, 64)]     # boxes nothing in the sky may touch: the coordinates

# ── Clouds (day) ─────────────────────────────────────────────────────────────

WIND_PERIOD = (11, 18)               # seconds for one crossing, rolled daily
CLOUDS_MIN, CLOUDS_EXTRA = 4, 2      # always 4, and on half of all days 2 more
LEAD_CLOUD_SCALE = (.85, 1.0)        # the first cloud is always a large one
CLOUD_SCALE = (.5, .85)
CLOUD_AREA = (52, 46, 848, 140)      # left, top, right, lowest base: the sky above the labels
CLOUD_GAP = 12                       # px clear between clouds at every point of their sway
SUN_CLEAR = 44                       # px from the sun's centre that free clouds stay out of
SUN_CLOUD = Cloud(758, 106, .55, reach=4)  # on cloudy days: always trims the sun's lower edge
SUN_CLOUD_CHANCE = .5

# ── Night sky ────────────────────────────────────────────────────────────────

STAR_COUNT = (10, 13)
STAR_AREA = (56, 52, 844, 152)       # left, top, right, bottom: the sky above the labels
STAR_SPACING = 48                    # px every star keeps from every other, so none clump
MOON_CLEAR = 30                      # px from the moon's centre

METEOR_COUNT = 10
METEOR_AREA = (52, 62, 848, 150)     # the whole streak, tail to end, stays inside
METEOR_MOON_CLEAR = 34

MOON_R = 10
MOON_MIN_LIT = .06                   # never thinner than a slim sliver, even at new moon
MOON_TILT = -25                      # degrees the lit side leans, for a natural look
SYNODIC_MONTH = 29.530588853         # days from one new moon to the next
NEW_MOON_EPOCH = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
MOON_VIEWING = time(14, 15)          # UTC; 20:00 in Nepal, when the phase is shown

AURORA_COLORS = ("#A3BE8C", "#8FBCBB")   # Nord green and frost
AURORA_BASE_Y = (196, 214)           # upper edge of the lower curtain; the ridge hides the rest
AURORA_WIDTH = (380, 600)            # px of sky each curtain covers
AURORA_OPACITY = (.10, .16)
AURORA_WAVE = (160, 260)             # px between folds; the folds flow sideways along the curtain
AURORA_FLOW = (22, 34)               # seconds for the folds to move one wave along

# Four satellites a day take turns, one per pass. Each flies its own arc and the
# whole craft (body and wings together) leans its own way.
SATELLITES = 4
SATELLITE_PASS = (25, 40)            # seconds to cross the sky, rolled daily
SATELLITE_GAP = (40, 80)             # seconds of clear sky between passes
SATELLITE_FIRST = (8, 20)            # seconds after load the first one appears
SATELLITE_Y = (74, 140)              # ends of the pass: below the coordinates, above the labels
SATELLITE_ARC = (18, 40)             # px the middle of the pass rises
SATELLITE_TOP = 58                   # the arc never rises above this
SATELLITE_LEAN = 25                  # degrees either way from level; the tumble adds up to 5 more
SATELLITE_TUMBLE = 5
SATELLITE_MOON_CLEAR = 26            # the moon's disc plus the craft's half-width
SATELLITE_HULL = "#D8DEE9"
SATELLITE_PANEL = "#5E81AC"
SATELLITE_TRIM = "#88C0D0"

# Four UFOs a day, by day and by night: each rises from behind the ridge, parks,
# comes a little closer, then whips off into the far sky until it is a dot and gone.
UFOS = 4
UFO_FIRST = (25, 45)                 # seconds after load the first one rises
UFO_GAP = (40, 180)                  # seconds of empty sky between flights
UFO_RISE, UFO_PARK = (2.2, 3.2), (3, 5)          # seconds, rolled daily
UFO_APPROACH, UFO_WHIP = (.6, .9), (1.1, 1.6)
UFO_APPROACH_SCALE = 1.6             # how much bigger it looks when it comes closer
UFO_PARK_Y = (178, 214)              # below the labels, above the ridge
UFO_ABOVE_RIDGE = 22                 # px it parks clear of the ridge line
UFO_CLEAR_OF_LEADERS = 30            # px from the summit leader lines
UFO_FAR_AREA = (70, 52, 830, 140)    # where in the sky it vanishes: left, top, right, bottom
UFO_WHIP_MIN = 240                   # px at least between parking and vanishing
UFO_COLORS = {                       # the hull is darker by day so it shows against white
    "light": dict(hull="#4C566A", dome="#88C0D0", light="#EBCB8B"),
    "dark": dict(hull="#D8DEE9", dome="#88C0D0", light="#EBCB8B"),
}

# ── Day visitors ─────────────────────────────────────────────────────────────

# Birds, the parachute, the hang glider and the plane share one schedule: only one
# is ever in the sky, and after it leaves the sky stays empty for VISIT_GAP seconds.
VISIT_GAP = (5, 15)
VISIT_FIRST = 6.0                    # seconds after load the first visitor appears
VISIT_SCHEDULE = 180                 # at least this many seconds before the schedule repeats
OFFSTAGE = (24, 876)                 # x just outside the left and right edges
FLIGHT = {"birds": (9, 13), "parachute": (24, 32), "glider": (28, 38), "plane": (16, 22)}   # seconds
VISIT_Y = {"birds": (74, 140), "parachute": (66, 100), "glider": (70, 116), "plane": (58, 96)}
FLOCK_SIZE = (2, 4)

# The parachute, glider and plane each fly ROUTES routes a day, taken in turn. The
# mix of directions is rolled (at least one each way), and every route sits a little
# above or below the kind's height for the day.
ROUTE_KINDS = ("parachute", "glider", "plane")
ROUTES = 4
ROUTE_JITTER = 10                    # px a route sits above or below the day's height
SINK = {"birds": (-10, 10), "glider": (24, 60), "plane": (-14, 14)}   # px lost (+) or gained (-) crossing
PARACHUTE_LANDING_X = (110, 790)     # the day's landing spots are spread along the ridge
PARACHUTE_SPACING = 120              # px at least between two landing spots
PARACHUTE_MIN_DRIFT = 160            # px at least it drifts in, so it comes down gently
PARACHUTE_LANDING_Y = 360            # it sinks to here; the ridge hides it well before

VISITOR_INK = "#4C566A"
CANOPY = "#D08770"                   # parachute
GLIDER_WING = "#B48EAD"
CONTRAIL = "#C2CAD6"

# ── Timeline (seconds) ───────────────────────────────────────────────────────

# After the intro, one sequence plays once: labels glow in turn, light runs along
# the ridge, a ripple leaves the sun or moon. Then the header rests.
SEQUENCE_START = 4.0
LABEL_GLOW, LABEL_STAGGER = 1.4, 0.7   # each label, one after another
TRACE_AT, TRACE_LEN = 3.0, 2.4         # light along the ridge, after SEQUENCE_START
RIPPLE_AT, RIPPLE_LEN = 5.2, 2.64      # ring leaving the sun or moon, after SEQUENCE_START
