"""Validation rules for script payloads."""

from __future__ import annotations

from typing import Any


class ScriptValidator:
    """Validate required script content before rendering."""

    def validate(self, payload: Any) -> list[str]:
        if not isinstance(payload, dict):
            return ["payload must be an object"]

        errors: list[str] = []
        for field in ("title", "hook"):
            if not isinstance(payload.get(field), str) or not payload[field].strip():
                errors.append(f"{field} must be a non-empty string")

        sections = payload.get("sections")
        if not isinstance(sections, list) or len(sections) < 4:
            errors.append("sections must contain at least 4 items")
        elif any(not isinstance(section, str) or not section.strip() for section in sections):
            errors.append("sections cannot contain empty items")
        return errors
