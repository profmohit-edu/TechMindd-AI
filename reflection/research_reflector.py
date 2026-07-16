"""Reflection rules for research artifacts."""

from __future__ import annotations

from typing import Any


class ResearchReflector:
    """Critique research structure and insight quality."""

    def reflect(
        self,
        original: dict[str, Any],
        director_plan: dict[str, Any],
        quality_score: dict[str, Any],
        validation_results: dict[str, Any],
    ) -> dict[str, str]:
        _ = original, director_plan
        weak = [name for name, score in quality_score["criteria"].items() if score < 70]
        if not validation_results.get("valid", False) or weak:
            reason = "Strengthen research " + ", ".join(item.replace("_", " ") for item in weak)
            return {"decision": "improved", "feedback": reason}
        return {"decision": "accepted", "feedback": "Research meets the quality criteria"}
