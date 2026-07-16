"""Quality scoring for research artifacts."""

from __future__ import annotations

from typing import Any


class ResearchScorer:
    """Score research completeness, structure, insights, and readability."""

    def score(self, payload: dict[str, Any]) -> dict[str, float]:
        required = ("topic", "audience", "summary", "insights")
        completeness = 100.0 * sum(bool(payload.get(field)) for field in required) / len(required)

        summary = str(payload.get("summary", "")).strip()
        factual_structure = 50.0
        if len(summary.split()) >= 12:
            factual_structure += 25.0
        if any(mark in summary for mark in (".", ":", ";")):
            factual_structure += 15.0

        insights = [str(item).strip() for item in payload.get("insights", [])]
        insight_quality = 40.0
        if len({item.lower() for item in insights}) == len(insights):
            insight_quality += 20.0
        if insights and sum(len(item.split()) for item in insights) / len(insights) >= 6:
            insight_quality += 20.0

        words = summary.split()
        readability = 70.0
        if 12 <= len(words) <= 120:
            readability += 20.0

        return {
            "completeness": min(completeness, 100.0),
            "factual_structure": min(factual_structure, 100.0),
            "insight_quality": min(insight_quality, 100.0),
            "readability": min(readability, 100.0),
        }
