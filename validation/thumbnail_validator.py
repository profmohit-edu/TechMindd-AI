"""Validation rules for thumbnail payloads."""

from __future__ import annotations

from typing import Any


class ThumbnailValidator:
    """Validate required thumbnail content before rendering."""

    def validate(self, payload: Any) -> list[str]:
        if not isinstance(payload, dict):
            return ["payload must be an object"]

        errors: list[str] = []
        for field in ("headline", "subheadline", "visual_notes"):
            if not isinstance(payload.get(field), str) or not payload[field].strip():
                errors.append(f"{field} must be a non-empty string")
        return errors
