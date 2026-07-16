"""JSON writer plugin."""

from __future__ import annotations

import json
from typing import Any, Dict

from writers.base import BaseWriterPlugin


class JSONWriter(BaseWriterPlugin):
    writer_name = "json"
    file_extension = ".json"

    def transform(self, _rendered_content: str, context: Dict[str, Any]) -> str:
        # JSON output serializes the structured payload directly.
        payload = context.get("payload")
        if payload is None:
            payload = {}
        return f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n"
