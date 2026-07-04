"""Earth Similarity Index.

Two-parameter Schulze-Makuch (2011) form using planet radius and equilibrium
temperature, both relative to Earth. Returns None when neither input is
available. Values fall in [0, 1]; Earth is 1.0 by construction.
"""

from typing import Optional


EARTH_RADIUS_RATIO = 1.0
EARTH_EQ_TEMP_K = 255.0

WEIGHT_RADIUS = 0.57
WEIGHT_TEMP = 5.58


def _component(value: float, reference: float, weight: float) -> float:
    return (1.0 - abs(value - reference) / (value + reference)) ** (
        weight / (WEIGHT_RADIUS + WEIGHT_TEMP)
    )


def earth_similarity(
    radius_earth: Optional[float], eq_temp_k: Optional[float]
) -> Optional[float]:
    parts = []
    if radius_earth and radius_earth > 0:
        parts.append(_component(radius_earth, EARTH_RADIUS_RATIO, WEIGHT_RADIUS))
    if eq_temp_k and eq_temp_k > 0:
        parts.append(_component(eq_temp_k, EARTH_EQ_TEMP_K, WEIGHT_TEMP))
    if not parts:
        return None
    esi = 1.0
    for p in parts:
        esi *= p
    return round(esi, 3)
