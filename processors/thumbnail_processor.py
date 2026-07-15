"""Thumbnail processor implementation."""

from __future__ import annotations

from typing import Any, Dict


class ThumbnailProcessor:
    """Prepare thumbnail copy and art direction fields."""

    name = "thumbnail"

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            raise TypeError("thumbnail payload must be a dictionary")

        headline = payload.get("headline", "")
        subheadline = payload.get("subheadline", "")
        visual_notes = payload.get("visual_notes", "")

        return {
            "headline": headline,
            "subheadline": subheadline,
            "visual_notes": visual_notes,
            "raw": payload,
        }
