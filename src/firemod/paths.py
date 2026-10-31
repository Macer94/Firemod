from __future__ import annotations

import os
import sys
from pathlib import Path


def resource_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "resources"
    packaged = Path(__file__).resolve().parent / "resources"
    if packaged.exists():
        return packaged
    # Source tree and installed editable environments.
    candidate = Path(__file__).resolve().parents[2] / "resources"
    if candidate.exists():
        return candidate
    return Path(sys.prefix) / "share" / "firemod" / "resources"


def data_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    result = base / "Firemod"
    result.mkdir(parents=True, exist_ok=True, mode=0o700)
    return result
