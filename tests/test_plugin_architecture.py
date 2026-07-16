import os

os.environ.setdefault("OPENAI_API_KEY", "test")

from agents.registry import AgentRegistry
from core.template_pack_registry import TemplatePackRegistry
from exporters.factory import ExporterPluginFactory
from providers.provider_factory import ProviderFactory
from rag.retriever_factory import RetrieverFactory
from writers.factory import WriterPluginFactory


class DummyProvider:
    def generate_structured_json(self, **kwargs):  # type: ignore[no-untyped-def]
        return {"ok": True, "kwargs": kwargs}


def test_dynamic_provider_plugins_are_discoverable() -> None:
    factory = ProviderFactory()
    assert {"openai", "gemini"}.issubset(set(factory.supported_providers()))


def test_dynamic_agent_plugins_are_discoverable() -> None:
    registry = AgentRegistry(DummyProvider())
    names = set(registry.names())
    assert {"director", "research", "script", "seo", "thumbnail", "social"}.issubset(names)


def test_writer_exporter_and_retriever_plugins_are_discoverable() -> None:
    writers = set(WriterPluginFactory().supported_writers())
    exporters = set(ExporterPluginFactory().supported_exporters())
    retrievers = set(RetrieverFactory().supported_retrievers())

    assert {"markdown", "html", "json"}.issubset(writers)
    assert {"directory", "zip"}.issubset(exporters)
    assert {"chroma"}.issubset(retrievers)


def test_template_pack_discovery_lists_default_templates() -> None:
    registry = TemplatePackRegistry()
    templates = set(registry.template_names("default"))
    assert {"research.jinja2", "script.jinja2", "seo.jinja2", "thumbnail.jinja2", "social.jinja2"}.issubset(
        templates
    )

