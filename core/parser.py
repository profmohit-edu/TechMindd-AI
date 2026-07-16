"""Parser for validating and normalizing model output payload."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Dict, List


@dataclass
class ParsedPackagePlan:
    package_name: str
    files: List[Dict[str, Any]]


class ResponseParser:
    """Parse once and normalize a single structured JSON response."""

    REQUIRED_TOP_LEVEL_KEYS = {"package_name", "files"}

    def parse(self, payload: Dict[str, Any]) -> ParsedPackagePlan:
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dictionary")

        missing = self.REQUIRED_TOP_LEVEL_KEYS - set(payload.keys())
        if missing:
            raise ValueError(f"Missing top-level keys: {sorted(missing)}")

        package_name = payload.get("package_name")
        files = payload.get("files")

        if not isinstance(package_name, str) or not package_name.strip():
            raise ValueError("package_name must be a non-empty string")

        if not isinstance(files, list):
            raise ValueError("files must be a list")

        normalized_files: List[Dict[str, Any]] = []
        seen_paths: set[str] = set()
        for idx, entry in enumerate(files):
            if not isinstance(entry, dict):
                raise ValueError(f"files[{idx}] must be an object")

            path = entry.get("path")
            content = entry.get("content")

            if not isinstance(path, str) or not path.strip():
                raise ValueError(f"files[{idx}].path must be a non-empty string")
            normalized_path = PurePosixPath(path.strip().replace("\\", "/"))
            if normalized_path.is_absolute() or ".." in normalized_path.parts:
                raise ValueError(f"files[{idx}].path must stay within the package")
            if normalized_path.as_posix() in seen_paths:
                raise ValueError(f"files[{idx}].path duplicates an earlier output")
            seen_paths.add(normalized_path.as_posix())
            if not isinstance(content, str):
                raise ValueError(f"files[{idx}].content must be a string")

            normalized_files.append(
                {
                    "path": normalized_path.as_posix(),
                    "content": content,
                    "template": bool(entry.get("template", False)),
                    "context": entry.get("context") or {},
                }
            )

        return ParsedPackagePlan(package_name=package_name.strip(), files=normalized_files)
