"""Coordinates a full data refresh from both catalogues.

Runs in a worker thread from the UI. Each stage reports progress via a
callback so the UI can update a status label without polling.
"""

import datetime as _dt
import traceback
from typing import Callable, Optional

from . import classify, db, esi
from .sources import nasa, oec


ProgressFn = Callable[[str], None]


def _noop(_: str) -> None:
    pass


def _enrich(record: dict) -> dict:
    record["planet_type"] = classify.planet_type(record.get("radius_earth"))
    record["esi"] = esi.earth_similarity(
        record.get("radius_earth"), record.get("eq_temp_k")
    )
    return record


def refresh(progress: Optional[ProgressFn] = None) -> dict:
    report = progress or _noop
    counts = {"oec": 0, "nasa": 0, "errors": []}

    try:
        report("Downloading Open Exoplanet Catalogue...")
        raw = oec.fetch_snapshot()
        report("Parsing OEC...")
        with db.connect() as conn:
            for rec in oec.iter_records(raw):
                db.upsert(conn, _enrich(rec))
                counts["oec"] += 1
    except Exception as exc:  # noqa: BLE001 - reported to user
        counts["errors"].append(f"OEC: {exc}")
        traceback.print_exc()

    try:
        report("Downloading NASA Exoplanet Archive...")
        csv_text = nasa.fetch_csv()
        report("Parsing NASA archive...")
        with db.connect() as conn:
            for rec in nasa.iter_records(csv_text):
                db.upsert(conn, _enrich(rec))
                counts["nasa"] += 1
    except Exception as exc:  # noqa: BLE001
        counts["errors"].append(f"NASA: {exc}")
        traceback.print_exc()

    with db.connect() as conn:
        db.set_meta(conn, "last_sync", _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z")
        counts["total"] = db.count(conn)

    report(
        f"Done. {counts['total']} planets in the local database "
        f"(OEC +{counts['oec']}, NASA +{counts['nasa']})."
    )
    return counts
