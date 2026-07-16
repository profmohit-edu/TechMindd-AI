"""Validation rules for research payloads."""

from __future__ import annotations

from typing import Any


class ResearchValidator:
    """Validate required research content before rendering."""

    def validate(self, payload: Any) -> list[str]:
        if not isinstance(payload, dict):
            return ["payload must be an object"]

        errors: list[str] = []
        for field in ("topic", "audience", "summary"):
            if not isinstance(payload.get(field), str) or not payload[field].strip():
                errors.append(f"{field} must be a non-empty string")

        insights = payload.get("insights")
        if not isinstance(insights, list) or len(insights) != 3:
            errors.append("insights must contain exactly 3 items")
        elif any(not isinstance(insight, str) or not insight.strip() for insight in insights):
            errors.append("insights cannot contain empty items")
        return errors
