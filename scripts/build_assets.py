#!/usr/bin/env python3
"""Build the artwork for the GitHub profile README.

Writes four SVGs:

    landscape-light.svg  landscape-dark.svg   header: sky, ridge, summits, name
    legend-light.svg     legend-dark.svg      key for the three summits

    python3 scripts/build_assets.py                          # today's sky into assets/
    python3 scripts/build_assets.py --date 2026-10-28 --out dist

--date sets the moon phase and, unless --seed is given, seeds everything random:
clouds, wind, day visitors, stars, shooting stars, aurora and satellite. A daily
GitHub Action (.github/workflows/sky.yml) builds with the Nepal date and
publishes to the `output` branch, which is what the profile shows. Tunable values
live in profile_art/config.py.

Animation timeline (seconds after the image loads):

    0.0 – 3.2   intro, once      ridge draws, summits fade up, sun/moon rises
    3.2 – 4.8   sky, once        clouds or stars fade in
    5.0 →       loop, every 12s  labels glow → light runs along the ridge →
                                 ripple leaves the sun/moon → rest
    always      ambient          glow breathes, clouds sway, stars twinkle, aurora shimmers
    6.0 →       day visitors     birds, paraglider, plane take turns, 5–15s of empty sky between
    now & then  night visitors   shooting stars, a satellite pass
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from profile_art.config import THEMES
from profile_art.render import landscape, legend
from profile_art.sky import roll_sky

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--date", type=date.fromisoformat, default=date.today(),
                        help="YYYY-MM-DD; sets the moon phase (default: today)")
    parser.add_argument("--seed", help="rolls everything random (default: the date)")
    parser.add_argument("--out", type=Path, default=ASSETS, help="directory to write the SVGs to")
    args = parser.parse_args()
    seed = args.seed or args.date.isoformat()

    sky = roll_sky(seed, args.date)
    args.out.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        (args.out / f"landscape-{theme}.svg").write_text(landscape(theme, sky), encoding="utf-8")
        (args.out / f"legend-{theme}.svg").write_text(legend(theme), encoding="utf-8")

    sun = "cloud over the sun" if sky.cloudy_sun else "clear sun"
    print(f"sky '{seed}': {len(sky.clouds)} clouds, {sun}, wind {sky.wind:.1f}s, "
          f"{len(sky.visits)} visitors per {sky.visit_cycle:.0f}s, {len(sky.stars)} stars, "
          f"moon {sky.moon.lit:.0%} lit → {args.out}")


if __name__ == "__main__":
    main()
