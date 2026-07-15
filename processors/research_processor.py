"""Research processor implementation."""

from __future__ import annotations

from typing import Any, Dict


class ResearchProcessor:
    """Normalize research payload into template context."""

    name = "research"

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            raise TypeError("research payload must be a dictionary")

        topic = payload.get("topic", "")
        audience = payload.get("audience", "")
        summary = payload.get("summary", "")
        insights = payload.get("insights", [])
        if not isinstance(insights, list):
            insights = [insights]

        return {
            "title": topic,
            "topic": topic,
            "audience": audience,
            "summary": summary,
            "insights": insights,
            "raw": payload,
        }
