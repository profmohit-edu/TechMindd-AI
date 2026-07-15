import logging

from core.template_engine import TemplateEngine


def test_render_all_placeholders_present() -> None:
    engine = TemplateEngine()
    output = engine.render("Hello {name}, topic is {topic}", {"name": "Alice", "topic": "AI"})
    assert output == "Hello Alice, topic is AI"


def test_render_one_placeholder_missing_logs_warning(caplog) -> None:
    engine = TemplateEngine()

    with caplog.at_level(logging.WARNING):
        output = engine.render("Hello {name}, topic is {topic}", {"name": "Alice"})

    assert output == "Hello Alice, topic is {topic}"
    assert "Missing template placeholder: topic" in caplog.text


def test_render_multiple_placeholders_missing_logs_all(caplog) -> None:
    engine = TemplateEngine()

    with caplog.at_level(logging.WARNING):
        output = engine.render("{a} {b} {c}", {"a": "x"})

    assert output == "x {b} {c}"
    assert "Missing template placeholder: b" in caplog.text
    assert "Missing template placeholder: c" in caplog.text


def test_render_empty_context_keeps_placeholders_and_logs(caplog) -> None:
    engine = TemplateEngine()

    with caplog.at_level(logging.WARNING):
        output = engine.render("{topic} - {audience}", {})

    assert output == "{topic} - {audience}"
    assert "Missing template placeholder: topic" in caplog.text
    assert "Missing template placeholder: audience" in caplog.text
