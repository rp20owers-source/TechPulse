"""Explicit data-directory selection; a broken saved choice never silently resets data."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


def default_directory() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
    return (base / "TechPulse").expanduser().resolve()


def preference_path() -> Path:
    return default_directory() / "workspace.json"


def data_directory() -> Path:
    override = os.environ.get("TECHPULSE_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    pointer = preference_path()
    if not pointer.exists() and not pointer.is_symlink():
        return default_directory()
    try:
        if pointer.stat().st_size > 16_384:
            raise ValueError("Oversized workspace preference")
        value = json.loads(pointer.read_text(encoding="utf8"))
        if not isinstance(value, dict) or value.get("version") != 1:
            raise ValueError("Unsupported workspace preference")
        directory = Path(value["data_directory"])
        if not directory.is_absolute() or not (directory / "techpulse.db").is_file():
            raise ValueError("Saved data folder is missing its database")
        return directory.resolve()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ValueError(
            f"Cannot use the saved workspace in {pointer}. Choose a data folder to continue."
        ) from exc


def remember_directory(directory) -> None:
    # The startup controller calls this only after opening a validated workspace.
    directory = Path(directory).expanduser().resolve()
    if not (directory / "techpulse.db").is_file():
        raise ValueError("The selected folder has no TechPulse database")
    pointer = preference_path()
    pointer.parent.mkdir(parents=True, exist_ok=True)
    descriptor, filename = tempfile.mkstemp(prefix=".workspace-", suffix=".json", dir=pointer.parent)
    temporary = Path(filename)
    try:
        with os.fdopen(descriptor, "w", encoding="utf8") as stream:
            json.dump({"version": 1, "data_directory": str(directory)}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, pointer)
    finally:
        temporary.unlink(missing_ok=True)
