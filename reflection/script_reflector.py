"""Reflection rules for script artifacts."""

from __future__ import annotations

from typing import Any


class ScriptReflector:
    """Critique script hook, flow, engagement, and completeness."""

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
            reason = "Improve script " + ", ".join(item.replace("_", " ") for item in weak)
            return {"decision": "improved", "feedback": reason}
        return {"decision": "accepted", "feedback": "Script meets the quality criteria"}
