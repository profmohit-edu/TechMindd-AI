"""Factory wiring for provider-parser-processors-template-writer pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict

import config
from agents.registry import AgentRegistry
from core.asset_manager import AssetManager
from core.package_writer import PackageWriter
from core.parser import ResponseParser
from core.template_engine import TemplateEngine
from core.writer import Writer
from observability import configure_logging
from plugins import PluginManager
from providers.provider_factory import ProviderFactory
from quality import ArtifactQuality, QualityError, QualityManager
from reflection import ReflectionDecision, ReflectionManager
from rag.ingestion import IngestionPipeline
from rag.paths import discover_documents, resolve_embeddings_dir, set_active_documents_dir
from validation import ValidationError, ValidationManager
from workflows import Workflow, WorkflowEngine


LOGGER = logging.getLogger("techmindd.factory")


@dataclass
class PipelineFactory:
    provider: Any
    parser: ResponseParser
    template_engine: TemplateEngine
    writer: Writer
    package_writer: PackageWriter
    processors: dict


def build_factory(provider_priority: list[str] | None = None) -> PipelineFactory:
    provider_factory = ProviderFactory()
    provider = provider_factory.managed_provider(priority=provider_priority)
    parser = ResponseParser()
    template_engine = TemplateEngine()
    writer = Writer()
    package_writer = PackageWriter(template_engine=template_engine, writer=writer)
    processors = {
        plugin.name(): plugin.processor()
        for plugin in PluginManager().discover().all()
    }

    return PipelineFactory(
        provider=provider,
        parser=parser,
        template_engine=template_engine,
        writer=writer,
        package_writer=package_writer,
        processors=processors,
    )


def _compute_documents_state(knowledge_path: Path) -> str:
    hashes: list[str] = []
    for path in discover_documents(knowledge_path):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        hashes.append(f"{path.relative_to(knowledge_path)}:{digest}")
    return "\n".join(hashes)


def _ensure_knowledge_index(knowledge_path: Path) -> None:
    if not config.settings.rag_enabled:
        return

    knowledge_path = set_active_documents_dir(knowledge_path)
    embeddings_path = resolve_embeddings_dir(knowledge_path)
    state_file = embeddings_path / "documents.sha256"

    current_state = _compute_documents_state(knowledge_path)
    previous_state = state_file.read_text(encoding="utf-8") if state_file.exists() else None
    db_missing = not embeddings_path.exists() or not any(embeddings_path.glob("*.sqlite*"))

    if not db_missing and previous_state == current_state:
        LOGGER.info("Knowledge base up-to-date; skipping ingestion")
        return

    LOGGER.info("Knowledge base missing or stale; starting ingestion")
    pipeline = IngestionPipeline(documents_dir=knowledge_path, embeddings_dir=embeddings_path)
    report = pipeline.ingest(knowledge_path)
    LOGGER.info("Ingestion completed: %d files updated", report.ingested_files)

    embeddings_path.mkdir(parents=True, exist_ok=True)
    state_file.write_text(current_state, encoding="utf-8")


def run_pipeline(
    *,
    topic: str,
    output_base_path: str = "output",
    knowledge_path: str | None = None,
    workflow: Workflow | None = None,
    progress_callback: Callable[[int, str], None] | None = None,
) -> Dict[str, Any]:
    def report_progress(progress: int, stage: str) -> None:
        if progress_callback is not None:
            progress_callback(progress, stage)

    started_at = time.perf_counter()
    report_progress(5, "initializing")
    if knowledge_path:
        _ensure_knowledge_index(Path(knowledge_path))

    provider_priority = None
    if workflow is not None and workflow.provider != "auto":
        configured = list(config.settings.provider_priority)
        provider_priority = [
            workflow.provider,
            *[name for name in configured if name != workflow.provider],
        ]
    factory = (
        build_factory()
        if provider_priority is None
        else build_factory(provider_priority=provider_priority)
    )

    provider = factory.provider

    LOGGER.info(
        "Using provider: %s",
        provider.__class__.__name__,
    )

    registry = AgentRegistry(provider)
    plugins = registry.plugins() if hasattr(registry, "plugins") else []
    plugin_by_name = {plugin.name(): plugin for plugin in plugins}
    available_plugin_names = [plugin.name() for plugin in plugins] or list(factory.processors)
    active_workflow = workflow or Workflow.implicit(available_plugin_names, output_base_path)
    missing_plugins = [name for name in active_workflow.plugins if name not in available_plugin_names]
    if missing_plugins:
        raise ValueError(f"Workflow references unavailable plugins: {', '.join(missing_plugins)}")
    plugin_names = list(active_workflow.plugins)
    validation_manager = ValidationManager(
        {plugin.name(): plugin.validator() for plugin in plugins} or None
    )
    quality_manager = QualityManager(
        scorers={plugin.name(): plugin.scorer() for plugin in plugins} or None
    )
    reflection_manager = ReflectionManager(
        {plugin.name(): plugin.reflector() for plugin in plugins} or None
    )

    LOGGER.info("Running DirectorAgent")
    report_progress(15, "director")
    director_plan = registry.get("director").generate(topic)
    LOGGER.info("Director plan generated")

    def _generate_agent(name: str, topic: str) -> tuple[str, Any, ArtifactQuality]:
        agent = registry.get(name)
        payload = agent.generate(topic, director_plan)
        if active_workflow.validation:
            try:
                validation_manager.validate(name, payload)
            except ValidationError:
                LOGGER.warning("Retrying %s agent after validation failure", name)
                payload = agent.generate(topic, director_plan)
                validation_manager.validate(name, payload)
        quality = (
            quality_manager.score(name, payload)
            if active_workflow.quality
            else ArtifactQuality(name, 100.0, {}, ())
        )
        if active_workflow.quality:
            try:
                quality_manager.require_quality(quality)
            except QualityError:
                LOGGER.warning("Retrying %s agent after low quality score", name)
                payload = agent.generate(topic, director_plan)
                if active_workflow.validation:
                    validation_manager.validate(name, payload)
                quality = quality_manager.score(name, payload)
                quality_manager.require_quality(quality)
        return name, payload, quality

    LOGGER.info("Starting generation for topic: %s", topic)
    report_progress(25, "generating_artifacts")

    agent_payloads: Dict[str, Any] = {}
    quality_results: Dict[str, ArtifactQuality] = {}

    if active_workflow.parallel:
        LOGGER.info("Launching concurrent specialist agents")
    else:
        LOGGER.info("Launching sequential specialist agents")

    def _collect_result(
        name: str,
        generated: tuple[str, Any, ArtifactQuality],
    ) -> None:
        agent_name, payload, quality = generated
        agent_payloads[agent_name] = payload
        quality_results[agent_name] = quality
        LOGGER.info("Agent %s completed", agent_name)

    def _execute_and_collect(name: str, result_getter: Any) -> None:
        try:
            _collect_result(name, result_getter())
        except ValidationError:
            LOGGER.exception("Agent %s failed validation after one retry", name)
            raise
        except QualityError:
            LOGGER.exception("Agent %s failed quality scoring after one retry", name)
            raise
        except Exception as exc:  # pragma: no cover
            LOGGER.exception("Agent %s failed: %s", name, exc)
            raise RuntimeError(f"Required specialist agent failed: {name}") from exc

    if active_workflow.parallel:
        with ThreadPoolExecutor(max_workers=max(1, len(plugin_names))) as executor:
            futures = {
                executor.submit(_generate_agent, name, topic): name
                for name in plugin_names
            }
            for future in as_completed(futures):
                _execute_and_collect(futures[future], future.result)
    else:
        for name in plugin_names:
            _execute_and_collect(name, lambda name=name: _generate_agent(name, topic))

    report_progress(60, "artifacts_generated")

    reflection_decisions: Dict[str, ReflectionDecision] = {}
    regenerated_artifacts: list[str] = []
    if active_workflow.reflection:
        report_progress(65, "reflection")
    for name in plugin_names if active_workflow.reflection else []:
        decision = reflection_manager.reflect(
            name,
            agent_payloads[name],
            director_plan,
            quality_results[name],
            {"valid": True, "errors": []},
        )
        reflection_decisions[name] = decision
        if decision.decision != "improved":
            continue

        reflection_plan = dict(director_plan)
        focus_key = f"{name}_focus"
        existing_focus = str(reflection_plan.get(focus_key, "")).strip()
        reflection_plan[focus_key] = (
            f"{existing_focus}\nReflection feedback: {decision.feedback}".strip()
        )
        candidate = registry.get(name).generate(topic, reflection_plan)
        try:
            if active_workflow.validation:
                validation_manager.validate(name, candidate)
        except ValidationError:
            LOGGER.warning("Discarding invalid reflected candidate for %s", name)
            continue
        candidate_quality = quality_manager.score(name, candidate)
        if candidate_quality.score > quality_results[name].score:
            agent_payloads[name] = candidate
            quality_results[name] = candidate_quality
            regenerated_artifacts.append(name)
            LOGGER.info(
                "Accepted reflected candidate for %s: %.2f > %.2f",
                name,
                candidate_quality.score,
                decision.before_score,
            )
        else:
            LOGGER.info(
                "Kept original %s artifact: reflected score %.2f <= %.2f",
                name,
                candidate_quality.score,
                decision.before_score,
            )

    raw_package_name = str(director_plan.get("package_name", "")) or topic
    bundle = {
        "package_name": re.sub(r"[^a-z0-9]+", "-", raw_package_name.lower()).strip("-")[:64]
        or "output",
        "files": [],
    }

    for name in plugin_names:
        plugin = plugin_by_name.get(name)
        processor = plugin.processor() if plugin is not None else factory.processors[name]
        output_name = plugin.output_name() if plugin is not None else f"{name}.md"
        template_name = plugin.template() if plugin is not None else f"{name}.jinja2"
        processed_context = processor.process(agent_payloads[name])
        bundle["files"].append(
            {
                "path": output_name,
                "content": "",
                "template": True,
                "context": processed_context | {
                    "processor": name,
                    "template": template_name,
                },
            }
        )

    plan = factory.parser.parse(bundle)
    report_progress(80, "rendering")
    package_dir = Path(output_base_path).expanduser().resolve() / plan.package_name
    package_dir.mkdir(parents=True, exist_ok=True)
    written = factory.package_writer.write_package(plan.files, base_path=package_dir)
    quality_report = (
        quality_manager.write_report(package_dir, quality_results)[1]
        if active_workflow.quality
        else {"overall_score": None}
    )
    if active_workflow.reflection:
        reflection_manager.write_report(
            package_dir,
            reflection_decisions,
            quality_results,
            regenerated_artifacts,
        )

    report_progress(90, "packaging")

    provider_name = str(getattr(config.settings, "provider", provider.__class__.__name__))
    model_name = str(getattr(provider, "model", "unknown"))
    provider_metrics = provider.summary() if hasattr(provider, "summary") else {}
    usage = provider_metrics or getattr(provider, "last_usage", {}) or {}
    assets = AssetManager()
    assets.write_metadata(
        package_dir,
        topic,
        provider_name,
        model_name,
        execution_time=time.perf_counter() - started_at,
        prompt_tokens=int(usage.get("input_tokens", 0)),
        completion_tokens=int(usage.get("output_tokens", 0)),
        estimated_cost=float(usage.get("estimated_cost", 0.0)),
        provider_used=usage.get("provider_used", [provider_name]),
        provider_fallback=usage.get("provider_fallback", []),
        retries=int(usage.get("retries", 0)),
        overall_quality_score=(
            float(quality_report["overall_score"])
            if quality_report["overall_score"] is not None
            else None
        ),
        reflection_performed=active_workflow.reflection,
        regenerated_artifacts=regenerated_artifacts,
        final_quality_score=(
            float(quality_report["overall_score"])
            if quality_report["overall_score"] is not None
            else None
        ),
    )
    assets.write_manifest(package_dir, topic, provider_name, model_name)
    assets.create_zip(package_dir)
    LOGGER.info("Output package written successfully")

    return {
        "package_name": plan.package_name,
        "output_path": str(package_dir),
        "files_written": [str(path) for path in written],
        "file_count": len(written),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the TechMindd content pipeline")
    parser.add_argument("--topic", required=True, help="Content topic")
    parser.add_argument("--workflow", default=None, help="Workflow YAML name")
    parser.add_argument(
        "--output",
        "--output-dir",
        dest="output",
        default=None,
        help="Base output directory",
    )
    parser.add_argument(
        "--knowledge",
        default=None,
        help="Optional knowledge documents directory for RAG ingestion",
    )
    args = parser.parse_args()

    configure_logging()

    if args.workflow:
        result = WorkflowEngine().execute(
            args.workflow,
            topic=args.topic,
            runner=run_pipeline,
            output_override=args.output,
            knowledge_path=args.knowledge,
        )
    else:
        result = run_pipeline(
            topic=args.topic,
            output_base_path=args.output or "output",
            knowledge_path=args.knowledge,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
