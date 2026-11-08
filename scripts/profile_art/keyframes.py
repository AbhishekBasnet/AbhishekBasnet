"""Number formatting and keyframe helpers shared by every part of the renderer."""

from __future__ import annotations


def num(v: float) -> str:
    """Shortest clean form of a number: 12.0 → 12, 0.50 → .5"""
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s.replace("0.", ".", 1) if s.lstrip("-").startswith("0.") else s


def share(seconds: float, cycle: float) -> str:
    """A moment in a looping animation, as a keyframe percentage."""
    return f"{num(seconds / cycle * 100)}%"


def crossing(name: str, duration: float, cycle: float, peak: float = 1) -> str:
    """Keyframes for something that fades in, crosses for `duration` seconds and
    fades out, then waits out the rest of a `cycle`-second loop."""
    fade = 1.0
    return (f"@keyframes {name} {{ 0% {{ opacity: 0; transform: none; }} "
            f"{share(fade, cycle)}, {share(duration - fade, cycle)} {{ opacity: {num(peak)}; }} "
            f"{share(duration, cycle)}, 100% {{ opacity: 0; transform: translate(var(--dx), var(--dy)); }} }}")
