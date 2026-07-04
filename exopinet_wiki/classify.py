"""Classify a planet into a rough type from its radius in Earth radii.

Bands follow the common Kepler-era grouping; anything without a measured
radius falls back to `unknown`. The label is also the BMP filename stem.
"""

from typing import Optional


TYPES = (
    "terrestrial",
    "super-earth",
    "mini-neptune",
    "neptune-like",
    "gas-giant",
    "unknown",
)


def planet_type(radius_earth: Optional[float]) -> str:
    if radius_earth is None or radius_earth <= 0:
        return "unknown"
    if radius_earth < 1.25:
        return "terrestrial"
    if radius_earth < 2.0:
        return "super-earth"
    if radius_earth < 4.0:
        return "mini-neptune"
    if radius_earth < 6.0:
        return "neptune-like"
    return "gas-giant"


DISPLAY = {
    "terrestrial": "Terrestrial",
    "super-earth": "Super-Earth",
    "mini-neptune": "Mini-Neptune",
    "neptune-like": "Neptune-like",
    "gas-giant": "Gas giant",
    "unknown": "Unknown",
}
