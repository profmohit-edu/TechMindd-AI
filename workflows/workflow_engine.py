"""Workflow validation and runner coordination."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from plugins import PluginManager
from providers.provider_factory import ProviderFactory
from workflows.workflow import Workflow
from workflows.workflow_loader import WorkflowLoader


class WorkflowEngine:
    def __init__(self, loader: WorkflowLoader | None = None) -> None:
        self.loader = loader or WorkflowLoader()

    def load(self, name: str) -> Workflow:
        workflow = self.loader.load(name)
        available = set(PluginManager().discover().names())
        missing = [plugin for plugin in workflow.plugins if plugin not in available]
        if missing:
            raise ValueError(f"Workflow references unavailable plugins: {', '.join(missing)}")
        supported_providers = set(ProviderFactory().supported_providers())
        if workflow.provider != "auto" and workflow.provider not in supported_providers:
            raise ValueError(f"Workflow references unsupported provider: {workflow.provider}")
        return workflow

    def execute(
        self,
        workflow_name: str,
        *,
        topic: str,
        runner: Callable[..., dict[str, Any]],
        output_override: str | None = None,
        knowledge_path: str | None = None,
    ) -> dict[str, Any]:
        workflow = self.load(workflow_name)
        return runner(
            topic=topic,
            output_base_path=output_override or workflow.output,
            knowledge_path=knowledge_path,
            workflow=workflow,
        )
