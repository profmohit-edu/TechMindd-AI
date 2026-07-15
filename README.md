# TechMindd-AI

TechMindd-AI generates structured AI content packages (research, script, SEO, thumbnail, and social content) from a single topic prompt.

## Features

- Provider-driven JSON package generation
- Processor pipeline for content-specific context shaping
- Template-based package writing into output directories
- CLI entry point for one-command generation

## Project Structure

- `main.py` — minimal executable entry point
- `factory.py` — pipeline orchestration and CLI
- `providers/` — LLM provider abstraction + implementations
- `processors/` — domain-specific payload processors
- `core/` — parser, template engine, and writers
- `tests/` — test suite

## Requirements

- Python 3.10+
- OpenAI API key

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Set required values:

- `OPENAI_API_KEY` (required)
- `OPENAI_MODEL` (optional, default: `gpt-4o-mini`)
- `OPENAI_TIMEOUT_SECONDS` (optional, default: `60`)
- `OPENAI_TEMPERATURE` (optional, default: `0.2`)

## Usage

Run the generator:

```bash
python main.py --topic "Future of AI in Healthcare" --output-dir output
```

Optional flags:

- `--log-level` one of `DEBUG|INFO|WARNING|ERROR|CRITICAL`

Example output:

```json
{
  "package_name": "ai-in-healthcare",
  "files_written": [
    "output/ai-in-healthcare/research.md",
    "output/ai-in-healthcare/script.md",
    "output/ai-in-healthcare/seo.md",
    "output/ai-in-healthcare/thumbnail.md",
    "output/ai-in-healthcare/social.md"
  ],
  "file_count": 5,
  "output_dir": "/absolute/path/to/output"
}
```

## Development Notes

- Keep provider implementations behind the `BaseProvider` abstraction.
- Avoid changing processor contracts without updating the schema in `factory.py`.
- Use type hints and deterministic processor output for predictable templates.
