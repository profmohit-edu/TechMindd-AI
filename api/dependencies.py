"""API services and dependency providers."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any
from uuid import uuid4

import config
from observability.metrics import ACTIVE_JOBS, GENERATION_DURATION, GENERATION_JOBS
from workflows import WorkflowEngine

LOGGER = logging.getLogger("techmindd.api.jobs")


@dataclass
class JobRecord:
    job_id: str
    topic: str
    workflow: str
    provider: str
    status: str = "queued"
    progress: int = 0
    current_stage: str = "queued"
    result: dict[str, Any] | None = None
    error: str | None = None
    logs: list[str] = field(default_factory=lambda: ["Job queued"])


class JobService:
    """Thread-safe background generation and job tracking service."""

    def __init__(self, max_workers: int = 4, output_root: str | Path | None = None) -> None:
        configured_root = output_root or os.getenv("TECHMINDD_API_OUTPUT_DIR", "output/api")
        self.output_root = Path(configured_root).expanduser().resolve()
        self._jobs: dict[str, JobRecord] = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="techmindd-api-job",
        )
        self._workflows = WorkflowEngine()

    def create(
        self,
        topic: str,
        workflow_name: str,
        provider_override: str | None = None,
    ) -> JobRecord:
        workflow = self._workflows.load(workflow_name)
        provider = provider_override or workflow.provider
        record = JobRecord(
            job_id=uuid4().hex,
            topic=topic.strip(),
            workflow=workflow.name,
            provider=provider,
        )
        with self._lock:
            self._jobs[record.job_id] = record
            ACTIVE_JOBS.inc()
        context = copy_context()
        self._executor.submit(context.run, self._run, record.job_id)
        return self.get(record.job_id)

    def get(self, job_id: str) -> JobRecord:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                raise KeyError(job_id)
            return JobRecord(**asdict(record))

    def list(self) -> list[JobRecord]:
        with self._lock:
            return [JobRecord(**asdict(record)) for record in reversed(self._jobs.values())]

    def retry(self, job_id: str) -> JobRecord:
        record = self.get(job_id)
        provider = record.provider if record.provider in {"auto", "openai", "gemini"} else None
        return self.create(record.topic, record.workflow, provider)

    def package_dir(self, job_id: str) -> Path:
        record = self.get(job_id)
        if record.status != "completed" or record.result is None:
            raise RuntimeError(record.status)
        return Path(str(record.result["output_path"])).resolve()

    def metadata(self, job_id: str) -> dict[str, Any]:
        path = self.package_dir(job_id) / "metadata.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def shutdown(self) -> None:
        """Stop accepting work and gracefully finish submitted jobs."""
        self._executor.shutdown(wait=True, cancel_futures=False)

    def _update(self, job_id: str, **changes: Any) -> None:
        with self._lock:
            record = self._jobs[job_id]
            for key, value in changes.items():
                setattr(record, key, value)

    def _progress(self, job_id: str, progress: int, stage: str) -> None:
        with self._lock:
            record = self._jobs[job_id]
            record.progress = progress
            record.current_stage = stage
            record.logs.append(f"{progress}% · {stage.replace('_', ' ')}")

    def _run(self, job_id: str) -> None:
        # Generation dependencies include local embedding models; defer them so
        # API startup and health probes remain fast and side-effect free.
        from factory import run_pipeline

        record = self.get(job_id)
        started = time.monotonic()
        try:
            workflow = self._workflows.load(record.workflow)
            if record.provider != "auto":
                workflow = replace(workflow, provider=record.provider)
            job_output = self.output_root / job_id
            self._update(
                job_id,
                status="running",
                progress=1,
                current_stage="starting",
                logs=[*record.logs, "1% · starting"],
            )
            result = run_pipeline(
                topic=record.topic,
                output_base_path=str(job_output),
                workflow=workflow,
                progress_callback=lambda progress, stage: self._progress(job_id, progress, stage),
            )
            metadata_path = Path(result["output_path"]) / "metadata.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            provider_used = metadata.get("provider_used") or record.provider
            provider_label = (
                ",".join(provider_used) if isinstance(provider_used, list) else str(provider_used)
            )
            self._update(
                job_id,
                status="completed",
                progress=100,
                current_stage="completed",
                provider=provider_label,
                result=result,
                logs=[*self.get(job_id).logs, "100% · completed"],
            )
            GENERATION_JOBS.labels("completed", record.workflow).inc()
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Background generation job failed: %s", job_id)
            self._update(
                job_id,
                status="failed",
                current_stage="failed",
                error=str(exc),
                logs=[*self.get(job_id).logs, f"Failed · {exc}"],
            )
            GENERATION_JOBS.labels("failed", record.workflow).inc()
        finally:
            ACTIVE_JOBS.dec()
            GENERATION_DURATION.labels(record.workflow).observe(time.monotonic() - started)


_JOB_SERVICE = JobService()


def get_job_service() -> JobService:
    return _JOB_SERVICE


def provider_health() -> list[dict[str, Any]]:
    priority = list(config.settings.provider_priority)
    configured = {
        "openai": bool(config.settings.openai_api_key),
        "gemini": bool(config.settings.gemini_api_key),
    }
    return [
        {
            "name": name,
            "configured": is_configured,
            "priority": priority.index(name) + 1 if name in priority else None,
            "health": "available" if is_configured else "not_configured",
        }
        for name, is_configured in configured.items()
    ]
