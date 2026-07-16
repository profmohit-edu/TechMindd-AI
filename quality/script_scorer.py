"""Quality scoring for script artifacts."""

from __future__ import annotations

from typing import Any


class ScriptScorer:
    """Score script hook, flow, engagement, and completeness."""

    def score(self, payload: dict[str, Any]) -> dict[str, float]:
        hook = str(payload.get("hook", "")).strip()
        sections = [str(item).strip() for item in payload.get("sections", [])]

        hook_strength = 40.0 + (20.0 if len(hook.split()) >= 2 else 0.0)
        if "?" in hook or "!" in hook:
            hook_strength += 20.0

        flow = 60.0
        if len({section.lower() for section in sections}) == len(sections):
            flow += 20.0
        if sections and sum(len(section.split()) for section in sections) / len(sections) >= 5:
            flow += 20.0

        engagement = 60.0
        combined = " ".join([hook, *sections]).lower()
        if any(term in combined for term in ("you", "imagine", "why", "how", "discover")):
            engagement += 20.0
        if len(combined.split()) >= 30:
            engagement += 20.0

        section_completeness = min(100.0, len(sections) * 25.0)
        return {
            "hook_strength": min(hook_strength, 100.0),
            "flow": min(flow, 100.0),
            "engagement": min(engagement, 100.0),
            "section_completeness": section_completeness,
        }
