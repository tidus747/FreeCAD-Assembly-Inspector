"""Resource helpers."""

from __future__ import annotations

from pathlib import Path


def get_icon_path(filename: str) -> str:
    """Return absolute icon path if it exists, else empty string."""
    base = Path(__file__).resolve().parent / "resources" / "icons"
    candidate = base / filename
    return str(candidate) if candidate.exists() else ""

