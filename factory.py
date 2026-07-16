"""Factory wiring for provider-parser-processors-template-writer pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import config
from agents.registry import AgentRegistry
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


def _response_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["package_name", "files"],
        "properties": {
            "package_name": {"type": "string"},
            "files": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["path", "content", "template", "context"],
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                        "template": {"type": "boolean"},
                        "context": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["processor", "payload"],
                            "properties": {
                                "processor": {
                                    "type": "string",
                                    "enum": ["research", "script", "seo", "thumbnail", "social"],
                                },
                                "payload": {
                                    "type": "object"
                                },
                            },
                        },
                    },
                },
            },
        },
    }


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


def run_pipeline(*, topic: str, output_base_path: str, knowledge_path: str | None = None) -> Dict[str, Any]:
    if knowledge_path:
        _ensure_knowledge_index(Path(knowledge_path))

    factory = build_factory()

    provider = factory.provider

    LOGGER.info(
        "Using provider: %s",
        provider.__class__.__name__,
    )

    registry = AgentRegistry(provider)

    def _generate_agent(name: str, topic: str) -> tuple[str, Any]:
        agent = registry.get(name)
        payload = agent.generate(topic)
        return name, payload

    LOGGER.info("Starting generation for topic: %s", topic)

    agent_order = ["research", "script", "seo", "thumbnail", "social"]
    agent_payloads: Dict[str, Any] = {}
    failed_agents = []

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
                failed_agents.append(name)
                LOGGER.exception("Agent %s failed: %s", name, exc)

    if failed_agents:
        LOGGER.warning("Some agents failed and will be excluded: %s", ", ".join(failed_agents))

    bundle = {
        "package_name": re.sub(r"[^a-z0-9]+", "_", topic.lower()).strip("_")[:48] or "output",
        "files": [],
    }

    for name in agent_order:
        payload = agent_payloads.get(name)
        if payload is None:
            continue
        bundle["files"].append(
            {
                "path": f"{name}.json",
                "content": json.dumps(payload, ensure_ascii=False, indent=2),
                "template": False,
                "context": {
                    "processor": name,
                    "payload": payload,
                },
            }
        )

    return bundle


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
