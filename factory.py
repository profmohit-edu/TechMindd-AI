"""Factory wiring for provider-parser-processors-template-writer pipeline."""

from __future__ import annotations

import argparse
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

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
from providers.openai_provider import OpenAIProvider


LOGGER = logging.getLogger("techmindd.factory")


@dataclass
class PipelineFactory:
    provider: OpenAIProvider
    parser: ResponseParser
    template_engine: TemplateEngine
    writer: Writer
    package_writer: PackageWriter
    processors: dict


def build_factory() -> PipelineFactory:
    provider = OpenAIProvider()
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


def run_pipeline(*, topic: str, output_base_path: str) -> Dict[str, Any]:
    factory = build_factory()

    provider = OpenAIProvider()
    registry = AgentRegistry(provider)

    LOGGER.info("Starting generation for topic: %s", topic)

    research = registry.get("research").generate(topic)
    script = registry.get("script").generate(topic)
    seo = registry.get("seo").generate(topic)
    thumbnail = registry.get("thumbnail").generate(topic)
    social = registry.get("social").generate(topic)

    package_slug = re.sub(r"-+", "-", topic.strip().lower().replace(" ", "-"))
    package_slug = re.sub(r"[^a-z0-9-]", "", package_slug)

    payload = {
        "package_name": package_slug,
        "files": [
            {
                "path": "research.md",
                "template": True,
                "content": "",
                "context": {
                    "processor": "research",
                    "payload": research,
                },
            },
            {
                "path": "script.md",
                "template": True,
                "content": "",
                "context": {
                    "processor": "script",
                    "payload": script,
                },
            },
            {
                "path": "seo.md",
                "template": True,
                "content": "",
                "context": {
                    "processor": "seo",
                    "payload": seo,
                },
            },
            {
                "path": "thumbnail.md",
                "template": True,
                "content": "",
                "context": {
                    "processor": "thumbnail",
                    "payload": thumbnail,
                },
            },
            {
                "path": "social.md",
                "template": True,
                "content": "",
                "context": {
                    "processor": "social",
                    "payload": social,
                },
            },
        ],
    }
    LOGGER.info("Generated package payload via AgentRegistry")

    parsed = factory.parser.parse(payload)
    LOGGER.info("Parsed package plan: %s (%d files)", parsed.package_name, len(parsed.files))

    package_slug = re.sub(r"-+", "-", parsed.package_name.strip().lower().replace(" ", "-"))
    package_slug = re.sub(r"[^a-z0-9-]", "", package_slug)
    file_map = {
        "research": "research.md",
        "script": "script.md",
        "seo": "seo.md",
        "thumbnail": "thumbnail.md",
        "social": "social.md",
    }

    processed_files = []
    for file_spec in parsed.files:
        context = dict(file_spec.get("context") or {})
        processor_name = context.get("processor")
        processor_input = context.get("payload", {})

        if processor_name and processor_name in factory.processors:
            context.update(factory.processors[processor_name].process(processor_input))
            file_spec["context"] = context

        if processor_name in file_map:
            file_spec["path"] = f"{package_slug}/{file_map[processor_name]}"

        processed_files.append(file_spec)

    output_dir = Path(output_base_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    written_paths = factory.package_writer.write_package(
        files=processed_files,
        base_path=output_dir,
    )

    LOGGER.info("Wrote %d files to %s", len(written_paths), output_dir)

    return {
        "package_name": parsed.package_name,
        "files_written": [str(path) for path in written_paths],
        "file_count": len(written_paths),
        "output_dir": str(output_dir.resolve()),
    }


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run TechMindd-AI content package generation")
    parser.add_argument("--topic", required=True, help="Topic to generate content for")
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory where generated files are written (default: output)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)",
    )
    return parser


def main() -> int:
    args = _build_arg_parser().parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    result = run_pipeline(topic=args.topic, output_base_path=args.output_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
