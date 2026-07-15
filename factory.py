"""Factory wiring for provider-parser-processors-template-writer pipeline."""

from __future__ import annotations

from dataclasses import dataclass

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
