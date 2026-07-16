"""Validation rules for social payloads."""

from __future__ import annotations

from typing import Any


class SocialValidator:
    """Validate required social content before rendering."""

    def validate(self, payload: Any) -> list[str]:
        if not isinstance(payload, dict):
            return ["payload must be an object"]

        errors: list[str] = []
        caption = payload.get("caption")
        if not isinstance(caption, str) or not caption.strip():
            errors.append("caption must be a non-empty string")

        hashtags = payload.get("hashtags")
        if not isinstance(hashtags, list) or len(hashtags) < 3:
            errors.append("hashtags must contain at least 3 items")
        elif any(not isinstance(hashtag, str) or not hashtag.strip() for hashtag in hashtags):
            errors.append("hashtags cannot contain empty items")
        return errors
