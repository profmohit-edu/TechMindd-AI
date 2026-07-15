"""End-to-end execution entrypoint for one-shot package generation."""

from __future__ import annotations

from typing import Any, Dict

from factory import build_factory


def run_pipeline(
    *,
    system_prompt: str,
    user_prompt: str,
    response_schema: Dict[str, Any],
    output_base_path: str = ".",
) -> Dict[str, Any]:
    """Run provider->parser->processors->template->writer pipeline once."""
    factory = build_factory()

    # One OpenAI request only
    payload = factory.provider.generate_structured_json(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_schema=response_schema,
    )

    # Parse once
    parsed = factory.parser.parse(payload)

    processed_files = []
    for file_spec in parsed.files:
        context = dict(file_spec.get("context") or {})
        processor_name = context.get("processor")
        processor_input = context.get("payload", {})

        if processor_name and processor_name in factory.processors:
            context.update(factory.processors[processor_name].process(processor_input))
            file_spec["context"] = context

        processed_files.append(file_spec)

    written_paths = factory.package_writer.write_package(
        files=processed_files,
        base_path=output_base_path,
    )

    return {
        "package_name": parsed.package_name,
        "files_written": [str(path) for path in written_paths],
        "file_count": len(written_paths),
    }
