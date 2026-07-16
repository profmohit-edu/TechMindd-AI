import os

os.environ.setdefault("OPENAI_API_KEY", "test")

import logging
from pathlib import Path
from typing import Any

import pytest

import factory
from agents.research_agent import ResearchAgent
from agents.script_agent import ScriptAgent
from agents.seo_agent import SEOAgent
from agents.social_agent import SocialAgent
from agents.thumbnail_agent import ThumbnailAgent
from core.parser import ResponseParser


class RecordingProvider:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def generate_structured_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, Any],
        temperature: float = 0.0,
        max_output_tokens: int | None = None,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response_schema": response_schema,
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
            }
        )
        return {"ok": True}


@pytest.mark.parametrize(
    ("agent_cls", "focus_key", "focus_label"),
    [
        (ResearchAgent, "research_focus", "Research focus"),
        (ScriptAgent, "script_focus", "Script focus"),
        (SEOAgent, "seo_focus", "SEO focus"),
        (ThumbnailAgent, "thumbnail_focus", "Thumbnail focus"),
        (SocialAgent, "social_focus", "Social focus"),
    ],
)
def test_specialist_agents_preserve_prompt_without_director_plan_and_append_focus_when_present(
    agent_cls: type[Any],
    focus_key: str,
    focus_label: str,
) -> None:
    provider = RecordingProvider()
    agent = agent_cls(provider)
    topic = "Artificial Intelligence for Engineering Students"
    director_plan = {focus_key: "Prioritize practical applications"}

    agent.generate(topic)
    assert provider.calls[-1]["user_prompt"] == f"Topic: {topic}"

    agent.generate(topic, director_plan)
    assert (
        provider.calls[-1]["user_prompt"]
        == f"Topic: {topic}\n{focus_label}: Prioritize practical applications"
    )


def test_run_pipeline_uses_director_plan_for_specialists_and_logs_flow(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    topic = "Artificial Intelligence for Engineering Students"
    director_plan = {
        "package_name": "ai-for-engineering-students",
        "audience": "Engineering Students",
        "tone": "Clear",
        "goal": "Teach",
        "research_focus": "Applications",
        "script_focus": "Narrative arc",
        "seo_focus": "Search intent",
        "thumbnail_focus": "Bold contrast",
        "social_focus": "Student-friendly hooks",
    }
    call_order: list[str] = []

    class FakeAgent:
        def __init__(self, name: str) -> None:
            self.name = name
            self.calls: list[tuple[str, dict[str, Any] | None]] = []

        def generate(
            self,
            topic: str,
            director_plan_arg: dict[str, Any] | None = None,
        ) -> dict[str, Any]:
            self.calls.append((topic, director_plan_arg))
            call_order.append(self.name)
            if self.name == "director":
                return director_plan

            payloads = {
                "research": {
                    "topic": topic,
                    "audience": "Engineering Students",
                    "summary": "Summary",
                    "insights": ["One", "Two", "Three"],
                },
                "script": {
                    "title": "Title",
                    "hook": "Hook",
                    "sections": ["One", "Two", "Three", "Four"],
                },
                "seo": {
                    "title": "SEO Title",
                    "description": "Description",
                    "keywords": ["one", "two", "three"],
                },
                "thumbnail": {
                    "headline": "Headline",
                    "subheadline": "Subheadline",
                    "visual_notes": "Visuals",
                },
                "social": {
                    "caption": "Caption",
                    "hashtags": ["#one", "#two", "#three"],
                },
            }
            return payloads[self.name]

    fake_agents = {
        name: FakeAgent(name)
        for name in ["director", "research", "script", "seo", "thumbnail", "social"]
    }

    class FakeRegistry:
        def __init__(self, provider: object) -> None:
            self.provider = provider

        def get(self, name: str) -> FakeAgent:
            return fake_agents[name]

    class IdentityProcessor:
        def process(self, payload: dict[str, Any]) -> dict[str, Any]:
            return payload

    class FakePackageWriter:
        def __init__(self) -> None:
            self.files: list[dict[str, Any]] = []

        def write_package(self, files: list[dict[str, Any]], base_path: Path) -> list[Path]:
            self.files = list(files)
            return [Path(base_path) / file_spec["path"] for file_spec in self.files]

    package_writer = FakePackageWriter()
    pipeline_factory = factory.PipelineFactory(
        provider=object(),
        parser=ResponseParser(),
        template_engine=None,
        writer=None,
        package_writer=package_writer,
        processors={
            "research": IdentityProcessor(),
            "script": IdentityProcessor(),
            "seo": IdentityProcessor(),
            "thumbnail": IdentityProcessor(),
            "social": IdentityProcessor(),
        },
    )

    monkeypatch.setattr(factory, "build_factory", lambda: pipeline_factory)
    monkeypatch.setattr(factory, "AgentRegistry", FakeRegistry)

    with caplog.at_level(logging.INFO):
        result = factory.run_pipeline(topic=topic, output_base_path=str(tmp_path))

    assert call_order[0] == "director"
    for name in ["research", "script", "seo", "thumbnail", "social"]:
        assert fake_agents[name].calls == [(topic, director_plan)]
    assert result["file_count"] == 5
    assert len(package_writer.files) == 5
    assert "Running DirectorAgent" in caplog.text
    assert "Director plan generated" in caplog.text
    assert "Launching concurrent specialist agents" in caplog.text
    assert "Output package written successfully" in caplog.text
