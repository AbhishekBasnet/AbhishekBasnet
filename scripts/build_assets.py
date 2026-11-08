#!/usr/bin/env python3
"""Build the artwork for the GitHub profile README.

Writes six SVGs:

    landscape-light.svg  landscape-dark.svg   profile header: sky, ridge, summits, name
    legend-light.svg     legend-dark.svg      key for the three summits
    backdrop-light.svg   backdrop-dark.svg    portfolio site backdrop: sky and ridge only

    python3 scripts/build_assets.py                          # today's sky into assets/
    python3 scripts/build_assets.py --date 2026-10-28 --out dist

--date sets the moon phase and, unless --seed is given, seeds everything random:
clouds, wind, day visitors, UFOs, stars, shooting stars, aurora and satellites. A daily
GitHub Action (.github/workflows/sky.yml) builds with the Nepal date and
publishes to the `output` branch, which is what the profile shows. Tunable values
live in profile_art/config.py.

Animation timeline (seconds after the image loads):

    0.0 – 3.2   intro, once      ridge draws, summits fade up, sun/moon rises
    3.2 – 4.8   sky, once        clouds or stars fade in
    4.0 – 7.5   sequence, once   labels glow in turn
    always      ambient          clouds sway, stars twinkle, muffler waves
    4.5 →       day visitors     birds, parachute, paraglider, plane take turns, 1–3s apart
    5 – 7 →     both             UFOs arrive, park and whip off, 6–12s apart
    4.5 →       night visitors   sky lanterns and the hot air balloon take turns, 1–3s apart;
                                 shooting stars; satellites from 3–5s, 3–8s apart; a comet from 25–45s, every 2.5–3.5 min
    2.8 – 5.4   climber, once    walks four strides up the devsecops peak, stops halfway
    5.4 →       climber          one gesture at a time: binoculars on each UFO by day, and
                                 shade / wave / photo / drink (day) or look / wave / photo / drink (night)
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from profile_art.config import THEMES
from profile_art.render import backdrop, landscape, legend
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
        (args.out / f"backdrop-{theme}.svg").write_text(backdrop(theme, sky), encoding="utf-8")

    sun = "cloud over the sun" if sky.cloudy_sun else "clear sun"
    print(f"sky '{seed}': {len(sky.clouds)} clouds, {sun}, wind {sky.wind:.1f}s, "
          f"{len(sky.visits)} visitors per {sky.visit_cycle:.0f}s, {len(sky.stars)} stars, "
          f"moon {sky.moon.lit:.0%} lit → {args.out}")


if __name__ == "__main__":
    main()
