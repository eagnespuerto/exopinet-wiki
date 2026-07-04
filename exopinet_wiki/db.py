"""SQLite storage for merged exoplanet records.

Schema: one row per planet, keyed by a canonical lowercase name. Fields from
either source are merged; the `sources` column records which catalogues
contributed. Numeric fields use NULL when unknown so the UI can sort/filter
sensibly.
"""

import sqlite3
from contextlib import contextmanager
from typing import Iterable, Iterator, Optional

from .paths import db_path


SCHEMA = """
CREATE TABLE IF NOT EXISTS planets (
    key             TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    host            TEXT,
    discovery_year  INTEGER,
    discovery_method TEXT,
    radius_earth    REAL,
    mass_earth      REAL,
    period_days     REAL,
    semimajor_au    REAL,
    eccentricity    REAL,
    eq_temp_k       REAL,
    star_spectype   TEXT,
    star_temp_k     REAL,
    star_distance_pc REAL,
    planet_type     TEXT,
    esi             REAL,
    sources         TEXT,
    updated_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_planets_name ON planets(name);
CREATE INDEX IF NOT EXISTS ix_planets_year ON planets(discovery_year);
CREATE INDEX IF NOT EXISTS ix_planets_esi  ON planets(esi);

CREATE TABLE IF NOT EXISTS meta (
    k TEXT PRIMARY KEY,
    v TEXT
);
"""


PLANET_COLS = (
    "key", "name", "host", "discovery_year", "discovery_method",
    "radius_earth", "mass_earth", "period_days", "semimajor_au",
    "eccentricity", "eq_temp_k", "star_spectype", "star_temp_k",
    "star_distance_pc", "planet_type", "esi", "sources",
)


def canonical_key(name: str) -> str:
    return " ".join(name.strip().lower().split())


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def upsert(conn: sqlite3.Connection, record: dict) -> None:
    """Insert or merge a planet record.

    Merge policy: keep existing non-null fields, fill in nulls from the new
    record, and append the new source label if not already present.
    """
    key = canonical_key(record["name"])
    record = {**record, "key": key}
    existing = conn.execute(
        "SELECT * FROM planets WHERE key = ?", (key,)
    ).fetchone()

    if existing is None:
        cols = ",".join(PLANET_COLS)
        placeholders = ",".join("?" for _ in PLANET_COLS)
        values = [record.get(c) for c in PLANET_COLS]
        conn.execute(
            f"INSERT INTO planets ({cols}) VALUES ({placeholders})", values
        )
        return

    merged = {}
    for col in PLANET_COLS:
        old = existing[col] if col in existing.keys() else None
        new = record.get(col)
        if col == "sources":
            merged[col] = _merge_sources(old, new)
        elif old in (None, "") and new not in (None, ""):
            merged[col] = new
        else:
            merged[col] = old

    set_clause = ",".join(f"{c} = ?" for c in PLANET_COLS if c != "key")
    values = [merged[c] for c in PLANET_COLS if c != "key"] + [key]
    conn.execute(
        f"UPDATE planets SET {set_clause}, updated_at = CURRENT_TIMESTAMP "
        f"WHERE key = ?",
        values,
    )


def _merge_sources(old: Optional[str], new: Optional[str]) -> Optional[str]:
    parts = set()
    for value in (old, new):
        if value:
            parts.update(p.strip() for p in value.split(",") if p.strip())
    return ",".join(sorted(parts)) if parts else None


def all_planets(
    conn: sqlite3.Connection,
    *,
    search: str = "",
    order_by: str = "name",
    descending: bool = False,
) -> Iterable[sqlite3.Row]:
    order_by = order_by if order_by in _SORTABLE else "name"
    direction = "DESC" if descending else "ASC"
    nulls = "NULLS LAST" if not descending else "NULLS LAST"
    if search:
        sql = (
            f"SELECT * FROM planets "
            f"WHERE name LIKE ? OR host LIKE ? "
            f"ORDER BY {order_by} {direction} {nulls}, name ASC"
        )
        wildcard = f"%{search}%"
        return conn.execute(sql, (wildcard, wildcard)).fetchall()
    sql = (
        f"SELECT * FROM planets "
        f"ORDER BY {order_by} {direction} {nulls}, name ASC"
    )
    return conn.execute(sql).fetchall()


def count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM planets").fetchone()[0]


def get_meta(conn: sqlite3.Connection, key: str) -> Optional[str]:
    row = conn.execute("SELECT v FROM meta WHERE k = ?", (key,)).fetchone()
    return row[0] if row else None


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta(k, v) VALUES(?, ?) "
        "ON CONFLICT(k) DO UPDATE SET v = excluded.v",
        (key, value),
    )


_SORTABLE = {
    "name",
    "host",
    "discovery_year",
    "radius_earth",
    "mass_earth",
    "period_days",
    "esi",
}
