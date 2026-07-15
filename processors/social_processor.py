"""Social processor implementation."""

from __future__ import annotations

from typing import Any, Dict, List


class SocialProcessor:
    """Normalize social captions and hashtag output."""

    name = "social"

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            raise TypeError("social payload must be a dictionary")

        caption = payload.get("caption", "")
        hashtags = payload.get("hashtags", [])

        if isinstance(hashtags, str):
            cleaned = hashtags.replace(",", " ")
            hashtag_list: List[str] = [h.strip() for h in cleaned.split() if h.strip()]
        elif isinstance(hashtags, list):
            hashtag_list = [str(h).strip() for h in hashtags if str(h).strip()]
        else:
            hashtag_list = []

        return {
            "caption": caption,
            "hashtags": hashtag_list,
            "hashtag_count": len(hashtag_list),
            "raw": payload,
        }
