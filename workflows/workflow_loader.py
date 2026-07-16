"""Safe YAML workflow loader."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from workflows.workflow import Workflow

_WORKFLOW_NAME = re.compile(r"^[a-zA-Z0-9_-]+$")


class WorkflowLoader:
    def __init__(self, workflows_dir: str | Path = "workflows") -> None:
        self.workflows_dir = Path(workflows_dir)

    def load(self, name: str) -> Workflow:
        if not _WORKFLOW_NAME.fullmatch(name):
            raise ValueError("workflow name contains unsupported characters")
        path = self.workflows_dir / f"{name}.yaml"
        if not path.is_file():
            raise FileNotFoundError(f"Workflow not found: {path}")
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        workflow = Workflow.from_dict(payload)
        if workflow.name != name:
            raise ValueError(
                f"Workflow name mismatch: requested {name}, YAML defines {workflow.name}"
            )
        return workflow
