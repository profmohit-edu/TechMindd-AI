"""SEO processor implementation."""

from __future__ import annotations

from typing import Any, Dict, List


class SEOProcessor:
    """Normalize SEO fields for templates."""

    name = "seo"

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            raise TypeError("seo payload must be a dictionary")

        title = payload.get("title", "")
        description = payload.get("description", "")
        keywords = payload.get("keywords", [])

        if isinstance(keywords, str):
            keyword_list: List[str] = [k.strip() for k in keywords.split(",") if k.strip()]
        elif isinstance(keywords, list):
            keyword_list = [str(k).strip() for k in keywords if str(k).strip()]
        else:
            keyword_list = []

        return {
            "title": title,
            "description": description,
            "keywords": ", ".join(keyword_list),
            "keyword_count": len(keyword_list),
            "raw": payload,
        }
