from pathlib import Path

import pytest

from api.middleware import ProductionMiddleware
from config import Settings
from core.parser import ResponseParser
from core.template_engine import TemplateEngine
from factory import _publish_package
from plugins import PluginManager
from providers.failover import ProviderManager


def test_auto_provider_configuration_uses_supported_priority(monkeypatch):
    monkeypatch.setenv("PROVIDER", "auto")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.delenv("PROVIDER_PRIORITY", raising=False)

    settings = Settings.from_env()

    assert settings.provider == "auto"
    assert settings.provider_priority == ("openai", "gemini")


def test_provider_manager_owns_retry_policy():
    class Provider:
        model = "test"
        timeout_seconds = 30
        max_retries = 4
        last_usage = {"total_tokens": 0}

        def generate_structured_json(self, **_request):
            assert self.max_retries == 0
            return {"ok": True}

    provider = Provider()
    manager = ProviderManager([("test", provider)], max_retries=0)

    assert manager.generate_structured_json() == {"ok": True}


@pytest.mark.parametrize("unsafe_path", ["../escape.md", "/tmp/escape.md", "a/../../b.md"])
def test_package_parser_rejects_paths_outside_package(unsafe_path):
    with pytest.raises(ValueError, match="stay within the package"):
        ResponseParser().parse(
            {"package_name": "safe", "files": [{"path": unsafe_path, "content": "x"}]}
        )


def test_template_engine_fails_when_template_is_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        TemplateEngine(tmp_path).render("missing.jinja2", {})


def test_plugin_discovery_is_complete_and_safe():
    registry = PluginManager().discover()

    assert {"research", "script", "seo", "thumbnail", "social", "demo"} <= set(registry.names())


def test_metric_paths_and_trace_ids_are_bounded():
    assert ProductionMiddleware._metric_path("/jobs/untrusted-id") == "/jobs/{job_id}"
    assert ProductionMiddleware._metric_path("/arbitrary/attacker/path") == "/unmatched"
    assert ProductionMiddleware._trace_id("valid.trace-id") == "valid.trace-id"
    assert ProductionMiddleware._trace_id("invalid id") != "invalid id"


def test_package_publication_replaces_stale_artifacts(tmp_path: Path):
    package = tmp_path / "package"
    package.mkdir()
    (package / "stale.md").write_text("stale", encoding="utf-8")
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "current.md").write_text("current", encoding="utf-8")

    _publish_package(staging, package)

    assert not (package / "stale.md").exists()
    assert (package / "current.md").read_text(encoding="utf-8") == "current"
