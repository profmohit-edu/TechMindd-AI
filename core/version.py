"""Application semantic version and build metadata."""

from __future__ import annotations

import os
from pathlib import Path


VERSION = Path(__file__).resolve().parents[1].joinpath("VERSION").read_text(encoding="utf-8").strip()
BUILD_SHA = os.getenv("BUILD_SHA", "development")
BUILD_DATE = os.getenv("BUILD_DATE", "unknown")


def build_metadata() -> dict[str, str]:
    return {"version": VERSION, "build_sha": BUILD_SHA, "build_date": BUILD_DATE}
