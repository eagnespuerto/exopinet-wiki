"""Open Exoplanet Catalogue reader.

Pulls the aggregated `systems.xml.gz` snapshot from the OEC GitHub mirror and
yields one dict per planet, using stdlib XML parsing only.
"""

import gzip
import io
import xml.etree.ElementTree as ET
from typing import Iterable, Optional

import requests


SNAPSHOT_URL = (
    "https://github.com/OpenExoplanetCatalogue/oec_gzip/raw/master/systems.xml.gz"
)

SOURCE_LABEL = "OEC"

# Earth reference values (SI: kg, m) — OEC uses Jupiter units for mass/radius.
JUPITER_MASS_TO_EARTH = 317.8
JUPITER_RADIUS_TO_EARTH = 11.209


def _float(el: Optional[ET.Element]) -> Optional[float]:
    if el is None or el.text is None:
        return None
    try:
        return float(el.text.strip())
    except ValueError:
        return None


def _int(el: Optional[ET.Element]) -> Optional[int]:
    v = _float(el)
    return int(v) if v is not None else None


def _text(el: Optional[ET.Element]) -> Optional[str]:
    if el is None or el.text is None:
        return None
    t = el.text.strip()
    return t or None


def fetch_snapshot(timeout: int = 60) -> bytes:
    resp = requests.get(SNAPSHOT_URL, timeout=timeout)
    resp.raise_for_status()
    return resp.content


def iter_records(raw_gz: bytes) -> Iterable[dict]:
    with gzip.open(io.BytesIO(raw_gz), "rb") as fh:
        xml_bytes = fh.read()
    root = ET.fromstring(xml_bytes)

    for system in root.findall("system"):
        distance_pc = _float(system.find("distance"))
        for star in system.findall("star"):
            star_name = _text(star.find("name"))
            star_temp = _float(star.find("temperature"))
            star_spec = _text(star.find("spectraltype"))
            for planet in star.findall("planet"):
                yield _planet_to_record(
                    planet,
                    host=star_name,
                    star_temp=star_temp,
                    star_spec=star_spec,
                    distance_pc=distance_pc,
                )
        # Some systems have planets directly under system (circumbinary etc.).
        for planet in system.findall("planet"):
            yield _planet_to_record(
                planet,
                host=_text(system.find("name")),
                star_temp=None,
                star_spec=None,
                distance_pc=distance_pc,
            )


def _planet_to_record(
    planet: ET.Element,
    *,
    host: Optional[str],
    star_temp: Optional[float],
    star_spec: Optional[str],
    distance_pc: Optional[float],
) -> dict:
    name = _text(planet.find("name")) or "Unnamed"
    mass_jup = _float(planet.find("mass"))
    radius_jup = _float(planet.find("radius"))
    period_days = _float(planet.find("period"))
    semimajor = _float(planet.find("semimajoraxis"))
    eccentricity = _float(planet.find("eccentricity"))
    eq_temp = _float(planet.find("temperature"))
    year = _int(planet.find("discoveryyear"))
    method = _text(planet.find("discoverymethod"))

    return {
        "name": name,
        "host": host,
        "discovery_year": year,
        "discovery_method": method,
        "radius_earth": (
            radius_jup * JUPITER_RADIUS_TO_EARTH if radius_jup is not None else None
        ),
        "mass_earth": (
            mass_jup * JUPITER_MASS_TO_EARTH if mass_jup is not None else None
        ),
        "period_days": period_days,
        "semimajor_au": semimajor,
        "eccentricity": eccentricity,
        "eq_temp_k": eq_temp,
        "star_spectype": star_spec,
        "star_temp_k": star_temp,
        "star_distance_pc": distance_pc,
        "sources": SOURCE_LABEL,
    }
