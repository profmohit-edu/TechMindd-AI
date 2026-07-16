"""Quality scoring for SEO artifacts."""

from __future__ import annotations

from typing import Any


class SEOScorer:
    """Score keyword, title, and description quality."""

    def score(self, payload: dict[str, Any]) -> dict[str, float]:
        title = str(payload.get("title", "")).strip()
        description = str(payload.get("description", "")).strip()
        keywords = [str(item).strip().lower() for item in payload.get("keywords", [])]

        keyword_quality = 50.0
        if len(set(keywords)) == len(keywords):
            keyword_quality += 40.0
        if any(" " in keyword for keyword in keywords):
            keyword_quality += 10.0

        title_quality = 70.0
        if 4 <= len(title.split()) <= 12:
            title_quality += 25.0
        if keywords and any(keyword in title.lower() for keyword in keywords):
            title_quality += 10.0

        description_quality = 70.0
        if 12 <= len(description.split()) <= 35:
            description_quality += 25.0
        if keywords and any(keyword in description.lower() for keyword in keywords):
            description_quality += 10.0

        return {
            "keyword_quality": min(keyword_quality, 100.0),
            "title_quality": min(title_quality, 100.0),
            "description_quality": min(description_quality, 100.0),
        }
