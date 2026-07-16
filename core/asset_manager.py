"""Asset management utilities for TechMindd-AI."""

from __future__ import annotations

import hashlib
import json
import subprocess
import zipfile
from datetime import datetime, UTC
from pathlib import Path
from typing import Any


class AssetManager:
    """Generates metadata, manifest and ZIP package."""

    @staticmethod
    def sha256(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def git_commit() -> str:
        try:
            return (
                subprocess.check_output(
                    ["git", "rev-parse", "--short", "HEAD"],
                    stderr=subprocess.DEVNULL,
                    text=True,
                )
                .strip()
            )
        except Exception:
            return "unknown"

    def write_manifest(
        self,
        package_dir: Path,
        topic: str,
        provider: str,
        model: str,
    ) -> Path:
        files: list[dict[str, Any]] = []

        for file in sorted(package_dir.glob("*")):
            if file.is_file():
                files.append(
                    {
                        "name": file.name,
                        "sha256": self.sha256(file),
                    }
                )

        manifest = {
            "package_name": package_dir.name,
            "topic": topic,
            "generated_at": datetime.now(UTC).isoformat(),
            "provider": provider,
            "model": model,
            "files": files,
        }

        manifest_path = package_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )
        return manifest_path

    def write_metadata(
        self,
        package_dir: Path,
        topic: str,
        provider: str,
        model: str,
        execution_time: float = 0.0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        estimated_cost: float = 0.0,
    ) -> Path:
        metadata = {
            "topic": topic,
            "provider": provider,
            "model": model,
            "execution_time": execution_time,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "estimated_cost": estimated_cost,
            "git_commit": self.git_commit(),
            "generated_at": datetime.now(UTC).isoformat(),
        }

        metadata_path = package_dir / "metadata.json"
        metadata_path.write_text(
            json.dumps(metadata, indent=2),
            encoding="utf-8",
        )
        return metadata_path

    def create_zip(self, package_dir: Path) -> Path:
        zip_path = package_dir / "package.zip"

        with zipfile.ZipFile(
            zip_path,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as archive:
            for file in sorted(package_dir.glob("*")):
                if file == zip_path:
                    continue
                if file.is_file():
                    archive.write(file, arcname=file.name)

        return zip_path
