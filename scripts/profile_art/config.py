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

SATELLITE_PASS = (25, 40)            # seconds to cross the sky
SATELLITE_GAP = (40, 80)             # seconds of clear sky between passes
SATELLITE_Y = (74, 130)              # below the coordinates, above the labels
SATELLITE_MOON_CLEAR = 28

# ── Day visitors ─────────────────────────────────────────────────────────────

# Birds, the paraglider and the plane share one schedule: only one is ever in the
# sky, and after it leaves the sky stays empty for VISIT_GAP seconds.
VISIT_GAP = (5, 15)
VISIT_FIRST = 6.0                    # seconds after load the first visitor appears
VISIT_SCHEDULE = 180                 # seconds of schedule rolled before it repeats
OFFSTAGE = (24, 876)                 # x just outside the left and right edges
FLIGHT = {"birds": (9, 13), "paraglider": (30, 40), "plane": (16, 22)}   # seconds to cross
VISIT_Y = {"birds": (74, 140), "paraglider": (70, 124), "plane": (58, 96)}
VISIT_DRIFT = {"birds": (-10, 10), "paraglider": (8, 20), "plane": (-6, 6)}
FLOCK_SIZE = (2, 4)

VISITOR_INK = "#4C566A"
CANOPY = "#D08770"
CONTRAIL = "#C2CAD6"

# ── Timeline (seconds) ───────────────────────────────────────────────────────

LOOP = 12.0
LOOP_START = 5.0
LABEL_GLOW, LABEL_STAGGER = 1.4, 0.7   # step 2: each label, one after another
TRACE_AT, TRACE_LEN = 3.0, 2.4         # step 3: light along the ridge
RIPPLE_AT, RIPPLE_LEN = 5.2, 2.64      # step 4: ring leaving the sun/moon
