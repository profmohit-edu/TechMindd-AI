"""Quality scoring for thumbnail artifacts."""

from __future__ import annotations

from typing import Any


class ThumbnailScorer:
    """Score thumbnail click potential, clarity, and brevity."""

    def score(self, payload: dict[str, Any]) -> dict[str, float]:
        headline = str(payload.get("headline", "")).strip()
        subheadline = str(payload.get("subheadline", "")).strip()
        visual_notes = str(payload.get("visual_notes", "")).strip()

        ctr_potential = 60.0
        combined = f"{headline} {subheadline}".lower()
        if any(term in combined for term in ("how", "why", "future", "secret", "explained")):
            ctr_potential += 20.0
        if "?" in combined or "!" in combined:
            ctr_potential += 20.0

        clarity = 70.0
        if len(visual_notes.split()) >= 2:
            clarity += 20.0
        if headline.lower() not in subheadline.lower():
            clarity += 10.0

        total_copy_words = len(headline.split()) + len(subheadline.split())
        brevity = 100.0 if total_copy_words <= 12 else max(40.0, 100.0 - (total_copy_words - 12) * 5.0)
        return {
            "ctr_potential": min(ctr_potential, 100.0),
            "clarity": min(clarity, 100.0),
            "brevity": brevity,
        }
