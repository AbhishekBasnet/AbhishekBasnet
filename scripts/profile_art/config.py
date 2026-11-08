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
                  orb="#BF616A", glow="#D08770"),
    "dark": dict(ink="#ECEFF4", muted="#8F9BB3", accent="#88C0D0", rule="#3B4252",
                 orb="#E5E9F0", glow="#E5E9F0"),
}
# The portfolio site (AbhishekBasnet.github.io) shows the same sky as a soft
# backdrop in its own palette, copied from its css/tokens.css. Its light page is
# grey-green, so clouds there are white to stand out.
SITE_THEMES = {
    "light": dict(ink="#2b3138", muted="#6b7680", accent="#4f7a94", rule="#d6dbd8",
                  orb="#BF616A", glow="#D08770"),
    "dark": dict(ink="#dfe4e2", muted="#94a0a8", accent="#8fb5cc", rule="#36404a",
                 orb="#E5E9F0", glow="#E5E9F0"),
}
SITE_CLOUD = "#FFFFFF"
BACKDROP_HEIGHT = 314                # just the sky and the ridge, without the caption below

SNOW = "#ECEFF4"
CLOUD_FILL = "#E5E9F0"

# ── Text ─────────────────────────────────────────────────────────────────────

NAME = "Abhishek Man Basnet"
ROLE = "backend engineer · nepal"
COORDS = "28.39° N   84.12° E"  # geographic centre of Nepal
TITLE = f"{NAME}, backend engineer and software engineering graduate, 2026 — flutter, devsecops, goLang"

LEGEND = [
    ("goLang", "services · concurrency · systems"),
    ("devsecops", "pipelines · security · infra"),
    ("flutter", "the clients on top"),
    ("grad", "software engineering · 2026"),
]

# ── Landscape ────────────────────────────────────────────────────────────────

RIDGE = [
    (48, 332), (110, 322), (150, 326), (200, 286), (236, 304), (270, 290), (296, 296),
    (336, 252), (378, 288), (476, 220), (504, 244), (526, 238), (560, 284),
    (604, 272), (652, 250), (690, 282), (740, 306), (790, 298), (852, 320),
]
# A label can run to two lines ("\n"): the first in the label style, the line under
# it smaller, so it fits between its neighbours. The last line sits on LABEL_Y.
SUMMITS = [(200, 286, "flutter"), (336, 252, "grad '26\nSoftware Engineering"),
           (476, 220, "devsecops"), (652, 250, "goLang")]
LABEL_Y = 170
LABEL_LINE_GAP = 14                  # px between the baselines of a two-line label
GROUND_Y = 342
ORB = (792, 92)                      # the sun by day, the moon by night
KEEP_CLEAR = [(40, 40, 224, 64),     # boxes nothing in the sky may touch: the coordinates,
              (292, 140, 380, 162)]  # and the upper line of the two-line summit label

# ── Climber ──────────────────────────────────────────────────────────────────

# A climber with a backpack walks up the straight left face of the devsecops peak
# (the ridge from (378, 288) to (476, 220)) and stops halfway, as if still on the
# way up. The muffler waves in the wind for good; at night a headlamp lights the way.
CLIMBER_X = (408, 427)               # x where the climber sets off and where they stop
CLIMBER_AT = 2.8                     # seconds after load they appear, once the ridge is drawn
CLIMBER_STRIDE = .65                 # seconds per stride
CLIMBER_STRIDES = 4                  # strides to the stop, so the walk lasts 2.6s
MUFFLER = "#D08770"                  # Nord orange, like the parachute and the sun's glow
HEADLAMP = "#EBCB8B"
# Once stopped, the climber passes the time with one gesture at a time, a short rest
# between. By day, whenever a UFO comes, they follow it through binoculars, and the
# other day gestures fill the gaps between UFOs. At night there are no binoculars;
# the gestures take turns in a loop. The order is shuffled daily.
CLIMBER_GESTURES = dict(shade=2.8, wave=2.2, photo=2.4, drink=2.8, look=5.0)   # seconds each
CLIMBER_DAY = ("shade", "wave", "photo", "drink")     # shade the eyes towards the sun, wave, take a photo, drink
CLIMBER_NIGHT = ("look", "wave", "photo", "drink")    # look around (the beam follows), wave, photo, drink
CLIMBER_REST = (1.5, 3.0)            # seconds between gestures
CLIMBER_RAISE = .4                   # seconds to bring the arm up or down
CLIMBER_BINOCULARS_LEAD = .3         # share of a UFO's arrival gone before the binoculars come up
CLIMBER_LOOKS = [(-26, 1), (10, 1), (0, -1)]   # look around: up, down, back; tilt in degrees (- is up), -1 faces back
CLIMBER_LOOK_TURN = .35              # seconds the head takes to turn to the next direction
BINOCULARS = "#4C566A"
GREETING = "Hi there!"               # the speech bubble that pops up while the climber waves
GREETING_SHOWN = 2                   # seconds it stays up
GREETING_TEXT = {"light": "#FFFFFF", "dark": "#2E3440"}   # on an ink bubble: white by day, dark at night
BOTTLE = "#8FBCBB"                   # Nord frost
UFO_CLEAR_OF_CLIMBER = 30            # px either side of the climber's walk that UFOs don't park in

# Footprints along the ridge crest from the left edge to the climber's heels: the
# peaks already climbed. They appear left to right as the ridge draws, and the last
# few under the climber's feet as they walk.
FOOTPRINT_SPACING = 6.5              # px along the ridge from one print to the next
FOOTPRINT_OFFSETS = (1.8, 3.6)       # px above the ridge line of the left and right foot
FOOTPRINT_TOE_OUT = 12               # degrees each print turns out from the direction of travel
FOOTPRINT_REVEAL = (1.0, 2.8)        # seconds the trail takes to reach where the climber sets off
FOOTPRINT_SUMMIT_CLEAR = 4.5         # px around a summit dot left bare

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

METEOR_COUNT = 6
METEOR_PERIOD = (14, 30)             # seconds between one meteor's appearances
METEOR_FLIGHT = (.6, 1.1)            # seconds a streak lasts, however often it comes
METEOR_FIRST, METEOR_SPREAD = 4.5, (5, 16)   # the first falls at 4.5s, the rest start within this window
METEOR_AREA = (52, 62, 848, 150)     # the whole streak, tail to end, stays inside
METEOR_MOON_CLEAR = 34

MOON_R = 10
MOON_MIN_LIT = .06                   # never thinner than a slim sliver, even at new moon
MOON_TILT = -25                      # degrees the lit side leans, for a natural look
SYNODIC_MONTH = 29.530588853         # days from one new moon to the next
NEW_MOON_EPOCH = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
MOON_VIEWING = time(14, 15)          # UTC; 20:00 in Nepal, when the phase is shown

# Four satellites a day take turns, one per pass. Each flies its own arc and the
# whole craft (body and wings together) leans its own way.
SATELLITES = 4
SATELLITE_PASS = (14, 20)            # seconds to cross the sky, rolled daily
SATELLITE_GAP = (3, 8)               # seconds of clear sky between passes
SATELLITE_FIRST = (3, 5)             # seconds after load the first one appears
SATELLITE_Y = (74, 140)              # ends of the pass: below the coordinates, above the labels
SATELLITE_ARC = (18, 40)             # px the middle of the pass rises
SATELLITE_TOP = 58                   # the arc never rises above this
SATELLITE_LEAN = 25                  # degrees either way from level; the tumble adds up to 5 more
SATELLITE_TUMBLE = 5
SATELLITE_MOON_CLEAR = 26            # the moon's disc plus the craft's half-width
SATELLITE_HULL = "#D8DEE9"
SATELLITE_PANEL = "#5E81AC"
SATELLITE_TRIM = "#88C0D0"

# Four UFOs a day, by day and by night. Each arrives, parks over the ridge, comes a
# little closer, then whips off into the far sky until it is a dot and gone. Some
# rise from behind the ridge and some swoop in from the far sky (at least one each).
UFOS = 4
UFO_FIRST = (5, 7)                   # seconds after load the first one arrives
UFO_GAP = (6, 12)                    # seconds of empty sky between flights
UFO_RISE, UFO_PARK = (1.8, 2.4), (2.5, 3.5)      # seconds to arrive and to stay parked, rolled daily
UFO_APPROACH, UFO_WHIP = (.6, .9), (1.1, 1.6)
UFO_APPROACH_SCALE = 1.6             # how much bigger it looks when it comes closer
UFO_PARK_Y = (178, 214)              # below the labels, above the ridge
UFO_ABOVE_RIDGE = 22                 # px it parks clear of the ridge line
UFO_CLEAR_OF_LEADERS = 30            # px from the summit leader lines
UFO_FAR_AREA = (70, 52, 830, 140)    # where in the sky it appears or vanishes: left, top, right, bottom
UFO_WHIP_MIN = 240                   # px at least between parking and the far point
UFO_PATHS_APART = 150                # px at least between where a sky arrival appears and where it vanishes
UFO_TING = .5                        # seconds the sparkle lasts where a UFO appears or vanishes
UFO_COLORS = {                       # the hull is darker by day so it shows against white
    "light": dict(hull="#4C566A", dome="#88C0D0", light="#EBCB8B", ting="#D08770"),
    "dark": dict(hull="#D8DEE9", dome="#88C0D0", light="#EBCB8B", ting="#ECEFF4"),
}

# ── Day visitors ─────────────────────────────────────────────────────────────

# Birds, the parachute, the paraglider and the plane share one schedule: only one
# is ever in the sky, and after it leaves the sky stays empty for VISIT_GAP seconds.
VISIT_GAP = (1, 3)
VISIT_FIRST = 4.5                    # seconds after load the first visitor appears
VISIT_SCHEDULE = 180                 # at least this many seconds before the schedule repeats
OFFSTAGE = (24, 876)                 # x just outside the left and right edges
FLIGHT = {"birds": (6, 8), "parachute": (10, 13), "paraglider": (11, 14), "plane": (9, 12)}   # seconds
VISIT_Y = {"birds": (74, 140), "parachute": (66, 100), "paraglider": (70, 116), "plane": (58, 96)}
FLOCK_SIZE = (2, 4)

# The parachute, paraglider and plane each fly ROUTES routes a day, taken in turn. The
# mix of directions is rolled (at least one each way), and every route sits a little
# above or below the kind's height for the day.
ROUTE_KINDS = ("parachute", "paraglider", "plane")
ROUTES = 4
ROUTE_JITTER = 10                    # px a route sits above or below the day's height
SINK = {"birds": (-10, 10), "plane": (-14, 14)}   # px lost (+) or gained (-) crossing

# The parachute and the paraglider come down behind the ridge at the day's landing
# spots: the parachute anywhere along it, the paraglider somewhere in the middle.
LANDINGS = {   # x range of the spots, px at least between spots, px below the ridge it aims for
    "parachute": dict(area=(110, 790), spacing=120, depth=70),
    "paraglider": dict(area=(300, 600), spacing=50, depth=24),   # shallow, so it glides rather than dives
}
LANDING_MIN_DRIFT = 160              # px at least it travels in, so it comes down gently
PARAGLIDER_GROWTH = 1.6              # how much bigger the paraglider gets as it comes towards us

VISITOR_INK = "#4C566A"
CANOPY = "#D08770"                   # parachute and paraglider
CONTRAIL = "#C2CAD6"

# ── Night visitors ───────────────────────────────────────────────────────────

# By night sky lanterns and a hot air balloon take turns the way the day visitors
# do: only one is ever in the sky, with VISIT_GAP seconds of empty sky after it,
# and neither follows itself.
NIGHT_FLIGHT = {"lanterns": (16, 20), "balloon": (24, 30)}   # seconds
LANTERN_SIZE = 1.7                   # lanterns are drawn this much larger than their outline, so they read
LANTERNS = (4, 7)                    # lanterns let go together
LANTERN_SPREAD = (24, 18)            # px the lanterns spread either side, and below the first
LANTERN_AREA = (120, 780)            # x along the ridge they rise from behind
LANTERN_TOP = (64, 100)              # y they have risen to when they fade out
LANTERN_DRIFT = (-50, 50)            # px sideways on the way up
# The balloon lifts off slowly from behind the ridge, climbs until its envelope
# reaches the labels, drifts a while, then sinks to land behind the ridge elsewhere.
BALLOON_AREA = (90, 810)             # x it lifts off from and lands at
BALLOON_HOP = (140, 260)             # px between lift-off and landing
BALLOON_TOP = (182, 196)             # y of the basket at the top of its climb; the envelope stands 23 px above
BALLOON_HOVER = .2                   # share of its flight it drifts at the top
BALLOON_SIZE = 1.07                  # the balloon and basket are drawn this much larger than their outline
NIGHT_INK = "#7B88A1"                # the balloon's envelope: moonlit grey, so it shows on the night sky
NIGHT_DARK = "#4C566A"               # the balloon's seams, ropes and basket
LANTERN_PAPER, LANTERN_GLOW = "#D08770", "#EBCB8B"

# Now and then a comet glides slowly across the upper sky.
COMET_FIRST = (25, 45)               # seconds after load it first appears
COMET_PERIOD = (150, 210)            # seconds between its appearances
COMET_FLIGHT = (9, 13)               # seconds it takes to glide its way
COMET_TRAVEL = (260, 360)            # px its head moves
COMET_TAIL = (60, 90)                # px of tail
COMET_AREA = (60, 48, 840, 132)      # the whole comet, tail to end, stays inside
COMET_MOON_CLEAR = 44
COMET_ION = "#8FBCBB"                # the faint ion tail, Nord frost

# ── Timeline (seconds) ───────────────────────────────────────────────────────

# After the intro the labels glow once, one after another. Then the header rests.
SEQUENCE_START = 4.0
LABEL_GLOW, LABEL_STAGGER = 1.4, 0.7   # each label, one after another
