"""Checks the sky rules hold across a year of daily seeds.

    python3 -m unittest discover -s scripts/tests -t scripts
"""

from __future__ import annotations

import datetime
import unittest
import xml.dom.minidom

from profile_art import config as cfg
from profile_art.geometry import contains, distance, height_on, overlaps
from profile_art.render import landscape, legend
from profile_art.sky import cloud_box, cloud_fits, meteor_fits, moon_on, roll_sky, satellite_path

DAYS = [datetime.date(2026, 1, 1) + datetime.timedelta(days=d) for d in range(365)]
SKIES = [roll_sky(day.isoformat(), day) for day in DAYS]


class CloudRules(unittest.TestCase):
    def test_count_is_the_minimum_or_minimum_plus_extra(self):
        for sky in SKIES:
            free = len(sky.clouds) - sky.cloudy_sun
            self.assertIn(free, (cfg.CLOUDS_MIN, cfg.CLOUDS_MIN + cfg.CLOUDS_EXTRA))

    def test_no_two_clouds_touch_at_any_point_of_their_sway(self):
        for sky in SKIES:
            boxes = [cloud_box(c) for c in sky.clouds]
            for i, a in enumerate(boxes):
                for b in boxes[i + 1:]:
                    self.assertFalse(overlaps(a, b))

    def test_free_clouds_stay_in_the_sky_and_off_the_sun(self):
        for sky in SKIES:
            for c in sky.clouds:
                if c != cfg.SUN_CLOUD:
                    self.assertTrue(cloud_fits(c, []))

    def test_sun_cloud_and_extra_clouds_each_appear_about_half_the_time(self):
        cloudy = sum(s.cloudy_sun for s in SKIES)
        extra = sum(len(s.clouds) - s.cloudy_sun > cfg.CLOUDS_MIN for s in SKIES)
        for n in (cloudy, extra):
            self.assertTrue(.4 < n / len(SKIES) < .6)

    def test_wind_stays_in_range(self):
        for sky in SKIES:
            self.assertTrue(cfg.WIND_PERIOD[0] <= sky.wind <= cfg.WIND_PERIOD[1])


class StarRules(unittest.TestCase):
    def test_stars_are_spaced_and_clear_of_moon_and_text(self):
        for sky in SKIES:
            self.assertTrue(cfg.STAR_COUNT[0] <= len(sky.stars) <= cfg.STAR_COUNT[1])
            for i, s in enumerate(sky.stars):
                p = (s.x, s.y)
                self.assertTrue(contains(cfg.STAR_AREA, p))
                self.assertGreaterEqual(distance(p, cfg.ORB), cfg.MOON_CLEAR)
                self.assertFalse(any(contains(k, p) for k in cfg.KEEP_CLEAR))
                for o in sky.stars[i + 1:]:
                    self.assertGreaterEqual(distance(p, (o.x, o.y)), cfg.STAR_SPACING)

    def test_brightest_star_comes_first(self):
        for sky in SKIES:
            self.assertEqual(sky.stars[0].r, max(s.r for s in sky.stars))

    def test_meteors_fit(self):
        for sky in SKIES:
            self.assertEqual(len(sky.meteors), cfg.METEOR_COUNT)
            self.assertTrue(all(meteor_fits(m) for m in sky.meteors))


class VisitorRules(unittest.TestCase):
    def test_one_visitor_at_a_time_with_5_to_15s_of_empty_sky_between(self):
        for sky in SKIES:
            ends = [v.start + sky.flight[v.kind] for v in sky.visits]
            starts = [v.start for v in sky.visits[1:]] + [sky.visit_cycle]   # the last waits for the loop
            for end, nxt in zip(ends, starts):
                self.assertTrue(cfg.VISIT_GAP[0] <= nxt - end <= cfg.VISIT_GAP[1])

    def test_every_kind_appears_and_none_follows_itself_even_across_the_loop(self):
        for sky in SKIES:
            kinds = [v.kind for v in sky.visits]
            self.assertEqual(set(kinds), set(cfg.FLIGHT))
            for a, b in zip(kinds, kinds[1:] + kinds[:1]):
                self.assertNotEqual(a, b)

    def test_each_flyer_flies_its_routes_mixed_directions_and_heights(self):
        for sky in SKIES:
            for kind in cfg.ROUTE_KINDS:
                routes = {v.route for v in sky.visits if v.kind == kind}
                self.assertEqual(len(routes), cfg.ROUTES)
                self.assertEqual({r.dx > 0 for r in routes}, {True, False})    # at least one each way
                heights = [r.y for r in routes]
                self.assertLessEqual(max(heights) - min(heights), 2 * cfg.ROUTE_JITTER)
                low, high = cfg.VISIT_Y[kind]
                self.assertTrue(all(low <= h <= high for h in heights))

    def test_landing_spots_are_spread_over_each_kinds_stretch_of_ridge(self):
        for sky in SKIES:
            for kind, rules in cfg.LANDINGS.items():
                spots = sorted({v.route.x + v.route.dx for v in sky.visits if v.kind == kind})
                self.assertEqual(len(spots), cfg.ROUTES)
                self.assertTrue(all(rules["area"][0] <= x <= rules["area"][1] for x in spots))
                self.assertTrue(all(b - a >= rules["spacing"] for a, b in zip(spots, spots[1:])))

    def test_visitors_enter_from_off_an_edge(self):
        for sky in SKIES:
            for v in sky.visits:
                self.assertIn(v.route.x, cfg.OFFSTAGE)
                if v.kind == "birds":
                    self.assertTrue(cfg.FLOCK_SIZE[0] <= len(v.flock) <= cfg.FLOCK_SIZE[1])

    def test_parachute_and_glider_land_behind_the_ridge(self):
        for sky in SKIES:
            for v in sky.visits:
                if v.kind in cfg.LANDINGS:
                    r = v.route
                    self.assertGreater(r.y + r.dy, height_on(cfg.RIDGE, r.x + r.dx))
                    self.assertGreaterEqual(abs(r.dx), cfg.LANDING_MIN_DRIFT)


class NightRules(unittest.TestCase):
    def test_moon_matches_known_phases(self):
        full, new, quarter = (moon_on(datetime.date.fromisoformat(d)) for d in ("2025-01-13", "2025-01-29", "2025-01-06"))
        self.assertAlmostEqual(full.phase, .5, delta=.04)
        self.assertLess(min(new.phase, 1 - new.phase), .04)
        self.assertAlmostEqual(quarter.phase, .25, delta=.04)

    def test_moon_never_thinner_than_a_sliver(self):
        for sky in SKIES:
            self.assertGreaterEqual(sky.moon.lit, cfg.MOON_MIN_LIT)

    def test_satellites_take_turns_on_arcs_clear_of_the_moon(self):
        for sky in SKIES:
            self.assertEqual(len(sky.satellites), cfg.SATELLITES)
            starts = [s.start for s in sky.satellites] + [sky.satellites[0].start + sky.satellite_cycle]
            for a, b in zip(starts, starts[1:]):
                self.assertTrue(cfg.SATELLITE_GAP[0] <= b - a - sky.satellite_pass <= cfg.SATELLITE_GAP[1])
            for s in sky.satellites:
                path = satellite_path(s)
                self.assertTrue(all(distance(p, cfg.ORB) >= cfg.SATELLITE_MOON_CLEAR for p in path))
                self.assertGreaterEqual(min(y for _, y in path), cfg.SATELLITE_TOP)
                self.assertTrue(cfg.SATELLITE_ARC[0] <= s.arc <= cfg.SATELLITE_ARC[1])
                self.assertLessEqual(abs(s.lean) + cfg.SATELLITE_TUMBLE, 30)
            self.assertTrue(cfg.SATELLITE_PASS[0] <= sky.satellite_pass <= cfg.SATELLITE_PASS[1])

    def test_ufos_arrive_both_ways_park_clear_and_vanish_in_the_sky(self):
        for sky in SKIES:
            self.assertEqual(len(sky.ufos), cfg.UFOS)
            self.assertEqual({u.arrive is None for u in sky.ufos}, {True, False})   # at least one of each
            visit = sum(sky.ufo_times)
            starts = [u.start for u in sky.ufos] + [sky.ufos[0].start + sky.ufo_cycle]
            for a, b in zip(starts, starts[1:]):
                self.assertTrue(cfg.UFO_GAP[0] <= b - a - visit <= cfg.UFO_GAP[1])
            for u in sky.ufos:
                ridge = height_on(cfg.RIDGE, u.x)
                self.assertGreater(u.y + u.rise, ridge)                       # a ridge arrival starts hidden
                self.assertGreaterEqual(ridge - u.y, cfg.UFO_ABOVE_RIDGE)     # parks clear
                if u.arrive:                                                  # a sky arrival appears far off
                    entry = (u.x + u.arrive[0], u.y + u.arrive[1])
                    self.assertTrue(contains(cfg.UFO_FAR_AREA, entry))
                    self.assertGreaterEqual(distance((u.x, u.y), entry), cfg.UFO_WHIP_MIN)
                    self.assertGreaterEqual(distance(entry, (u.x + u.dx, u.y + u.dy)), cfg.UFO_PATHS_APART)
                self.assertTrue(all(abs(u.x - sx) >= cfg.UFO_CLEAR_OF_LEADERS for sx, _, _ in cfg.SUMMITS))
                far = (u.x + u.dx, u.y + u.dy)                                # vanishes in the sky
                self.assertTrue(contains(cfg.UFO_FAR_AREA, far))
                self.assertGreaterEqual(distance((u.x, u.y), far), cfg.UFO_WHIP_MIN)

    def test_aurora_stays_inside_the_sky_and_has_room_to_flow(self):
        for sky in SKIES:
            self.assertEqual(len(sky.aurora), len(cfg.AURORA_COLORS))
            for rb in sky.aurora:
                self.assertTrue(cfg.LEFT <= rb.span[0] < rb.span[1] <= cfg.RIGHT)
                # the drawn edge reaches a full wave past the window on both sides
                self.assertLessEqual(rb.top[0][0], rb.span[0] - rb.wave + 1e-6)
                self.assertGreaterEqual(rb.top[-1][0], rb.span[1] + rb.wave - 1e-6)


class Output(unittest.TestCase):
    def test_same_seed_gives_same_sky(self):
        day = datetime.date(2026, 10, 28)
        self.assertEqual(roll_sky("2026-10-28", day), roll_sky("2026-10-28", day))

    def test_svgs_are_well_formed(self):
        for sky in SKIES[:30]:
            for theme in cfg.THEMES:
                xml.dom.minidom.parseString(landscape(theme, sky))
        for theme in cfg.THEMES:
            xml.dom.minidom.parseString(legend(theme))


if __name__ == "__main__":
    unittest.main()
