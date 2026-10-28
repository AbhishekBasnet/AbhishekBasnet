"""Checks the sky rules hold across a year of daily seeds.

    python3 -m unittest discover -s scripts/tests -t scripts
"""

from __future__ import annotations

import datetime
import unittest
import xml.dom.minidom

from profile_art import config as cfg
from profile_art.geometry import contains, distance, overlaps
from profile_art.render import landscape, legend
from profile_art.sky import cloud_box, cloud_fits, meteor_fits, roll_sky

DAYS = [str(datetime.date(2026, 1, 1) + datetime.timedelta(days=d)) for d in range(365)]
SKIES = [roll_sky(day) for day in DAYS]


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


class Output(unittest.TestCase):
    def test_same_seed_gives_same_sky(self):
        self.assertEqual(roll_sky("2026-10-28"), roll_sky("2026-10-28"))

    def test_svgs_are_well_formed(self):
        for theme in cfg.THEMES:
            xml.dom.minidom.parseString(landscape(theme, SKIES[0]))
            xml.dom.minidom.parseString(legend(theme))


if __name__ == "__main__":
    unittest.main()
