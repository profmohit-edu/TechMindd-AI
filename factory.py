"""Factory wiring for provider-parser-processors-template-writer pipeline."""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

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
                                "payload": {"type": "object", "additionalProperties": False},
                            },
                        },
                    },
                },
            },
        },
    }


def _build_prompts(topic: str) -> tuple[str, str]:
    system_prompt = (
        "You are TechMindd-AI content planner. Return ONLY valid JSON matching the schema. "
        "Generate exactly five files in outputs/{slug}/ with these filenames: "
        "research.md, script.md, seo.md, thumbnail.md, social.md. "
        "For each file set template=true and include Python-format placeholders in content that match context keys. "
        "Use processor values research/script/seo/thumbnail/social respectively, and provide payload fields required by each processor."
    )

    user_prompt = f"Create an AI content package for topic: {topic}."
    return system_prompt, user_prompt


def run_pipeline(*, topic: str, output_base_path: str) -> Dict[str, Any]:
    factory = build_factory()

    system_prompt, user_prompt = _build_prompts(topic)
    schema = _response_schema()

    LOGGER.info("Starting generation for topic: %s", topic)

    payload = factory.provider.generate_structured_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_schema=schema,
    )
    LOGGER.info("Received JSON response from OpenAI")

    parsed = factory.parser.parse(payload)
    LOGGER.info("Parsed package plan: %s (%d files)", parsed.package_name, len(parsed.files))

    processed_files = []
    for file_spec in parsed.files:
        context = dict(file_spec.get("context") or {})
        processor_name = context.get("processor")
        processor_input = context.get("payload", {})

        if processor_name and processor_name in factory.processors:
            context.update(factory.processors[processor_name].process(processor_input))
            file_spec["context"] = context

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
