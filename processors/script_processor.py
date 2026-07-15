"""Script processor implementation."""

from __future__ import annotations

from typing import Any, Dict, List


class ScriptProcessor:
    """Prepare script sections for local rendering."""

    name = "script"

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            raise TypeError("script payload must be a dictionary")

        title = payload.get("title", "")
        hook = payload.get("hook", "")
        sections = payload.get("sections", [])

        if not isinstance(sections, list):
            sections = [sections]

        normalized_sections: List[str] = [str(section) for section in sections]

        return {
            "title": title,
            "hook": hook,
            "sections": normalized_sections,
            "section_count": len(normalized_sections),
            "raw": payload,
        }
