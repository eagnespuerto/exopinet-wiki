import os
from pathlib import Path


def data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    path = Path(base) / "exopinet-wiki"
    path.mkdir(parents=True, exist_ok=True)
    return path


def db_path() -> Path:
    return data_dir() / "data.db"


def asset_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "assets"


def bmp_dir() -> Path:
    return asset_dir() / "bmp"
