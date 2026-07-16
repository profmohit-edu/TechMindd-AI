"""Validation rules for SEO payloads."""

from __future__ import annotations

from typing import Any


class SEOValidator:
    """Validate required SEO content before rendering."""

    def validate(self, payload: Any) -> list[str]:
        if not isinstance(payload, dict):
            return ["payload must be an object"]

        errors: list[str] = []
        for field in ("title", "description"):
            if not isinstance(payload.get(field), str) or not payload[field].strip():
                errors.append(f"{field} must be a non-empty string")

        keywords = payload.get("keywords")
        if not isinstance(keywords, list) or len(keywords) < 3:
            errors.append("keywords must contain at least 3 items")
        elif any(not isinstance(keyword, str) or not keyword.strip() for keyword in keywords):
            errors.append("keywords cannot contain empty items")
        return errors
