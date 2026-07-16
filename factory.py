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
from typing import Any, Dict

import config
from agents.registry import AgentRegistry
from core.asset_manager import AssetManager
from core.package_writer import PackageWriter
from core.parser import ResponseParser
from core.template_engine import TemplateEngine
from core.writer import Writer
from processors.research_processor import ResearchProcessor
from processors.script_processor import ScriptProcessor
from processors.seo_processor import SEOProcessor
from processors.social_processor import SocialProcessor
from processors.thumbnail_processor import ThumbnailProcessor
from providers.provider_factory import ProviderFactory
from rag.ingestion import IngestionPipeline
from rag.paths import discover_documents, resolve_embeddings_dir, set_active_documents_dir


LOGGER = logging.getLogger("techmindd.factory")


@dataclass
class PipelineFactory:
    provider: Any
    parser: ResponseParser
    template_engine: TemplateEngine
    writer: Writer
    package_writer: PackageWriter
    processors: dict


def build_factory() -> PipelineFactory:
    provider_factory = ProviderFactory()
    provider = provider_factory.default_provider()
    parser = ResponseParser()
    template_engine = TemplateEngine()
    writer = Writer()
    package_writer = PackageWriter(template_engine=template_engine, writer=writer)
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


def run_pipeline(*, topic: str, output_base_path: str, knowledge_path: str | None = None) -> Dict[str, Any]:
    started_at = time.perf_counter()
    if knowledge_path:
        _ensure_knowledge_index(Path(knowledge_path))

    factory = build_factory()

    provider = factory.provider

    LOGGER.info(
        "Using provider: %s",
        provider.__class__.__name__,
    )

    registry = AgentRegistry(provider)

    LOGGER.info("Running DirectorAgent")
    director_plan = registry.get("director").generate(topic)
    LOGGER.info("Director plan generated")

    def _generate_agent(name: str, topic: str) -> tuple[str, Any]:
        agent = registry.get(name)
        payload = agent.generate(topic, director_plan)
        return name, payload

    LOGGER.info("Starting generation for topic: %s", topic)

    agent_order = ["research", "script", "seo", "thumbnail", "social"]
    agent_payloads: Dict[str, Any] = {}

    LOGGER.info("Launching concurrent specialist agents")
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(_generate_agent, name, topic): name
            for name in agent_order
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                agent_name, payload = future.result()
                agent_payloads[agent_name] = payload
                LOGGER.info("Agent %s completed", agent_name)
            except Exception as exc:  # pragma: no cover
                LOGGER.exception("Agent %s failed: %s", name, exc)
                raise RuntimeError(f"Required specialist agent failed: {name}") from exc

    raw_package_name = str(director_plan.get("package_name", "")) or topic
    bundle = {
        "package_name": re.sub(r"[^a-z0-9]+", "-", raw_package_name.lower()).strip("-")[:64]
        or "output",
        "files": [],
    }

    for name in agent_order:
        processed_context = factory.processors[name].process(agent_payloads[name])
        bundle["files"].append(
            {
                "path": f"{name}.md",
                "content": "",
                "template": True,
                "context": processed_context | {"processor": name},
            }
        )

    plan = factory.parser.parse(bundle)
    package_dir = Path(output_base_path).expanduser().resolve() / plan.package_name
    package_dir.mkdir(parents=True, exist_ok=True)
    written = factory.package_writer.write_package(plan.files, base_path=package_dir)

    provider_name = str(getattr(config.settings, "provider", provider.__class__.__name__))
    model_name = str(getattr(provider, "model", "unknown"))
    usage = getattr(provider, "last_usage", {}) or {}
    assets = AssetManager()
    assets.write_metadata(
        package_dir,
        topic,
        provider_name,
        model_name,
        execution_time=time.perf_counter() - started_at,
        prompt_tokens=int(usage.get("input_tokens", 0)),
        completion_tokens=int(usage.get("output_tokens", 0)),
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
    parser.add_argument(
        "--output",
        "--output-dir",
        dest="output",
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
