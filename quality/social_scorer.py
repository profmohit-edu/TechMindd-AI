"""Quality scoring for social artifacts."""

from __future__ import annotations

from typing import Any


class SocialScorer:
    """Score social engagement, hashtags, and readability."""

    def score(self, payload: dict[str, Any]) -> dict[str, float]:
        caption = str(payload.get("caption", "")).strip()
        hashtags = [str(item).strip().lower() for item in payload.get("hashtags", [])]

        engagement = 60.0
        if any(mark in caption for mark in ("?", "!")):
            engagement += 20.0
        if any(term in caption.lower() for term in ("you", "learn", "discover", "share", "comment")):
            engagement += 20.0

        hashtag_quality = 60.0
        if len(set(hashtags)) == len(hashtags):
            hashtag_quality += 30.0
        if all(hashtag.startswith("#") for hashtag in hashtags):
            hashtag_quality += 10.0

        word_count = len(caption.split())
        readability = 80.0 if word_count <= 80 else max(40.0, 100.0 - (word_count - 80))
        if 5 <= word_count <= 40:
            readability = 100.0
        return {
            "engagement": min(engagement, 100.0),
            "hashtag_quality": min(hashtag_quality, 100.0),
            "readability": readability,
        }
