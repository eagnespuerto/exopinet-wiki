"""NASA Exoplanet Archive reader.

Queries the TAP service on the `pscomppars` table (composite planetary
parameters, one row per confirmed planet). Delivered as CSV so we can parse
with the stdlib and stream one dict per row.
"""

import csv
import io
from typing import Iterable, Optional

import requests


TAP_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

FIELDS = (
    "pl_name",
    "hostname",
    "disc_year",
    "discoverymethod",
    "pl_rade",
    "pl_bmasse",
    "pl_orbper",
    "pl_orbsmax",
    "pl_orbeccen",
    "pl_eqt",
    "st_spectype",
    "st_teff",
    "sy_dist",
)

QUERY = f"select {','.join(FIELDS)} from pscomppars"

SOURCE_LABEL = "NASA"


def _f(row: dict, key: str) -> Optional[float]:
    v = row.get(key)
    if v in (None, "", "NaN"):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _i(row: dict, key: str) -> Optional[int]:
    v = _f(row, key)
    return int(v) if v is not None else None


def _s(row: dict, key: str) -> Optional[str]:
    v = row.get(key)
    if v is None:
        return None
    v = v.strip()
    return v or None


def fetch_csv(timeout: int = 120) -> str:
    resp = requests.get(
        TAP_URL,
        params={"query": QUERY, "format": "csv"},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.text


def iter_records(csv_text: str) -> Iterable[dict]:
    reader = csv.DictReader(io.StringIO(csv_text))
    for row in reader:
        name = _s(row, "pl_name")
        if not name:
            continue
        yield {
            "name": name,
            "host": _s(row, "hostname"),
            "discovery_year": _i(row, "disc_year"),
            "discovery_method": _s(row, "discoverymethod"),
            "radius_earth": _f(row, "pl_rade"),
            "mass_earth": _f(row, "pl_bmasse"),
            "period_days": _f(row, "pl_orbper"),
            "semimajor_au": _f(row, "pl_orbsmax"),
            "eccentricity": _f(row, "pl_orbeccen"),
            "eq_temp_k": _f(row, "pl_eqt"),
            "star_spectype": _s(row, "st_spectype"),
            "star_temp_k": _f(row, "st_teff"),
            "star_distance_pc": _f(row, "sy_dist"),
            "sources": SOURCE_LABEL,
        }
