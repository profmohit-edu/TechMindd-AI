"""Factory wiring for provider-agent-processor-template-writer-exporter pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import config
from agents.registry import AgentRegistry
from core.package_writer import PackageWriter
from core.parser import ResponseParser
from core.template_engine import TemplateEngine
from core.writer import Writer
from exporters.base import BaseExporterPlugin
from exporters.factory import ExporterPluginFactory
from processors.research_processor import ResearchProcessor
from processors.script_processor import ScriptProcessor
from processors.seo_processor import SEOProcessor
from processors.social_processor import SocialProcessor
from processors.thumbnail_processor import ThumbnailProcessor
from providers.provider import BaseProvider
from providers.provider_factory import ProviderFactory
from rag.ingestion import IngestionPipeline
from writers.base import BaseWriterPlugin
from writers.factory import WriterPluginFactory


LOGGER = logging.getLogger("techmindd.factory")
_MAX_PACKAGE_NAME_LENGTH = 48


@dataclass
class PipelineFactory:
    provider: BaseProvider
    parser: ResponseParser
    template_engine: TemplateEngine
    writer: Writer
    package_writer: PackageWriter
    exporter: BaseExporterPlugin
    processors: dict[str, Any]


def build_factory() -> PipelineFactory:
    provider_factory = ProviderFactory()
    provider = provider_factory.default_provider()
    parser = ResponseParser()
    template_engine = TemplateEngine()
    writer = Writer()

    writer_plugin: BaseWriterPlugin = WriterPluginFactory().default_writer()
    package_writer = PackageWriter(
        template_engine=template_engine,
        writer=writer,
        writer_plugin=writer_plugin,
    )
    exporter = ExporterPluginFactory().default_exporter()

    processors = {
        "research": ResearchProcessor(),
        "script": ScriptProcessor(),
        "seo": SEOProcessor(),
        "thumbnail": ThumbnailProcessor(),
        "social": SocialProcessor(),
    }

    return PipelineFactory(
        provider=provider,
        parser=parser,
        template_engine=template_engine,
        writer=writer,
        package_writer=package_writer,
        exporter=exporter,
        processors=processors,
    )


def _compute_documents_state(knowledge_path: Path) -> str:
    if not knowledge_path.exists():
        return ""

    hashes: list[str] = []
    for path in sorted(knowledge_path.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".pdf", ".txt", ".md", ".markdown"}:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        hashes.append(f"{path.relative_to(knowledge_path)}:{digest}")
    return "\n".join(hashes)


def _ensure_knowledge_index(knowledge_path: Path) -> None:
    if not config.settings.rag_enabled:
        return

    embeddings_path = Path("knowledge/embeddings")
    state_file = embeddings_path / "documents.sha256"

    current_state = _compute_documents_state(knowledge_path)
    previous_state = state_file.read_text(encoding="utf-8") if state_file.exists() else None
    db_missing = not embeddings_path.exists() or not any(embeddings_path.glob("*.sqlite*"))

    if not db_missing and previous_state == current_state:
        LOGGER.info("Knowledge base up-to-date; skipping ingestion")
        return

    LOGGER.info("Knowledge base missing or stale; starting ingestion")
    pipeline = IngestionPipeline()
    ingested = pipeline.ingest(knowledge_path)
    LOGGER.info("Ingestion completed for %d files", ingested)

    embeddings_path.mkdir(parents=True, exist_ok=True)
    state_file.write_text(current_state, encoding="utf-8")


def run_pipeline(*, topic: str, output_base_path: str | Path, knowledge_path: str | None = None) -> dict[str, Any]:
    output_base_path = Path(output_base_path)
    if knowledge_path:
        _ensure_knowledge_index(Path(knowledge_path))

    factory = build_factory()

    provider = factory.provider
    LOGGER.info("Using provider: %s", provider.__class__.__name__)

    registry = AgentRegistry(provider)

    director_name = config.settings.director_agent
    specialist_order = list(config.settings.specialist_agents)

    LOGGER.info("Running DirectorAgent")
    director_plan = registry.get(director_name).generate(topic)
    LOGGER.info("Director plan generated")

    def _generate_agent(name: str, topic: str, plan: dict[str, Any]) -> tuple[str, Any]:
        agent = registry.get(name)
        payload = agent.generate(topic, plan)
        return name, payload

    LOGGER.info("Launching concurrent specialist agents")
    agent_payloads: dict[str, Any] = {}
    failed_agents: list[str] = []

    with ThreadPoolExecutor(max_workers=max(1, len(specialist_order))) as executor:
        futures = {
            executor.submit(_generate_agent, name, topic, director_plan): name
            for name in specialist_order
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                agent_name, payload = future.result()
                agent_payloads[agent_name] = payload
                LOGGER.info("Agent %s completed", agent_name)
            except Exception as exc:  # pragma: no cover
                failed_agents.append(name)
                LOGGER.exception("Agent %s failed: %s", name, exc)

    if failed_agents:
        LOGGER.warning("Some agents failed and will be excluded: %s", ", ".join(failed_agents))

    package_name = str(director_plan.get("package_name", "")).strip()
    if not package_name:
        package_name = (
            re.sub(r"[^a-z0-9]+", "_", topic.lower()).strip("_")[:_MAX_PACKAGE_NAME_LENGTH] or "output"
        )

    file_plan: list[dict[str, Any]] = []
    for name in specialist_order:
        payload = agent_payloads.get(name)
        if payload is None:
            continue

        processor = factory.processors.get(name)
        normalized_payload = processor.process(payload) if processor else payload
        context = {"processor": name, "payload": normalized_payload, **normalized_payload}

        file_plan.append(
            {
                "path": name,
                "content": json.dumps(normalized_payload, ensure_ascii=False, indent=2),
                "template": True,
                "template_name": f"{name}.jinja2",
                "context": context,
            }
        )

    package_dir = output_base_path / package_name
    files_written = factory.package_writer.write_package(file_plan, base_path=package_dir)
    export_result = factory.exporter.export(package_dir=package_dir, files_written=files_written)

    result = {
        "package_name": package_name,
        **export_result,
    }
    LOGGER.info("Output package written successfully")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the TechMindd content pipeline")
    parser.add_argument("--topic", required=True, help="Content topic")
    parser.add_argument(
        "--output",
        default="output",
        help="Base output directory",
    )
    parser.add_argument(
        "--knowledge",
        default=None,
        help="Optional knowledge documents directory for RAG ingestion",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")

    result = run_pipeline(topic=args.topic, output_base_path=args.output, knowledge_path=args.knowledge)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
