#!/usr/bin/env python3
"""Build the artwork for the GitHub profile README.

Writes four SVGs:

    landscape-light.svg  landscape-dark.svg   header: sky, ridge, summits, name
    legend-light.svg     legend-dark.svg      key for the three summits

    python3 scripts/build_assets.py                          # preview into assets/
    python3 scripts/build_assets.py --seed 2026-10-28 --out dist

The sky (cloud layout, wind, stars, shooting stars) is rolled from --seed. A daily
GitHub Action (.github/workflows/sky.yml) builds with the date as the seed and
publishes to the `output` branch, which is what the profile shows. Tunable values
live in profile_art/config.py.

Animation timeline (seconds after the image loads):

    0.0 – 3.2   intro, once      ridge draws, summits fade up, sun/moon rises
    3.2 – 4.8   sky, once        clouds or stars fade in
    5.0 →       loop, every 12s  labels glow → light runs along the ridge →
                                 ripple leaves the sun/moon → rest
    always      ambient          glow breathes, stars twinkle, clouds sway,
                                 shooting stars fall now and then (dark only)
"""

from __future__ import annotations

import argparse
from pathlib import Path

from profile_art.config import THEMES
from profile_art.render import landscape, legend
from profile_art.sky import roll_sky

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--seed", default="preview", help="rolls the sky; the daily build passes the date")
    parser.add_argument("--out", type=Path, default=ASSETS, help="directory to write the SVGs to")
    args = parser.parse_args()

    sky = roll_sky(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        (args.out / f"landscape-{theme}.svg").write_text(landscape(theme, sky), encoding="utf-8")
        (args.out / f"legend-{theme}.svg").write_text(legend(theme), encoding="utf-8")

    sun = "cloud over the sun" if sky.cloudy_sun else "clear sun"
    print(f"sky '{args.seed}': {len(sky.clouds)} clouds, {sun}, wind {sky.wind:.1f}s, "
          f"{len(sky.stars)} stars → {args.out}")


if __name__ == "__main__":
    main()
