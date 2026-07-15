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
        insights = payload.get("insights", [])
        if not isinstance(insights, list):
            insights = [str(insights)]

        formatted_insights = "\n".join(f"- {item}" for item in insights)

        return {
            "topic": topic,
            "audience": audience,
            "insights": formatted_insights,
            "raw": payload,
        }
