# TechMindd-AI

TechMindd-AI generates structured AI content packages (research, script, SEO, thumbnail, and social content) from a single topic prompt.

## Features

- Director-led multi-agent pipeline (strategic planning + specialist execution)
- Jinja2-based Markdown rendering via `TemplateEngine`
- Provider-driven structured JSON generation (agents stay data-only)
- Template-based package writing into output directories
- CLI entry point for one-command generation

## Project Structure

- `main.py` — minimal executable entry point
- `factory.py` — pipeline orchestration and CLI
- `providers/` — LLM provider abstraction + implementations
- `agents/` — director and specialist agents (return structured JSON only)
- `core/` — parser, template engine (`TemplateEngine`), and writers
- `templates/` — Jinja2 `.md.j2` document templates
- `tests/` — test suite

## Requirements

- Python 3.10+
- OpenAI API key (when `PROVIDER=openai`)
- Gemini API key (when `PROVIDER=gemini`)

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

- `PROVIDER` (`openai` or `gemini`, default: `openai`)
- `OPENAI_API_KEY` (required when `PROVIDER=openai`)
- `OPENAI_MODEL` (optional, default: `gpt-4o-mini`)
- `OPENAI_TIMEOUT_SECONDS` (optional, default: `60`)
- `OPENAI_TEMPERATURE` (optional, default: `0.2`)
- `GEMINI_API_KEY` (required when `PROVIDER=gemini`)
- `GEMINI_MODEL` (optional, default: `gemini-1.5-flash`)
- `GEMINI_TIMEOUT_SECONDS` (optional, default: `60`)
- `GEMINI_TEMPERATURE` (optional, default: `0.2`)

## Usage

Run the generator:

```bash
python factory.py --topic "Artificial Intelligence"
```

This produces rendered Markdown files in a slug-named subdirectory:

```
output/artificial-intelligence/
    research.md
    script.md
    seo.md
    thumbnail.md
    social.md
```

Example JSON summary printed to stdout:

```json
{
  "package_name": "artificial-intelligence",
  "file_count": 5,
  "output_path": "output/artificial-intelligence",
  "files": [
    "output/artificial-intelligence/research.md",
    "output/artificial-intelligence/script.md",
    "output/artificial-intelligence/seo.md",
    "output/artificial-intelligence/thumbnail.md",
    "output/artificial-intelligence/social.md"
  ]
}
```

Optional flags:

- `--output` — base output directory (default: `output`)
- `--knowledge` — optional path to knowledge documents directory for RAG ingestion

## Pipeline Architecture

```
Topic
  └─► DirectorAgent (strategic plan)
        └─► Specialist Agents (concurrent, JSON only)
              ├─ ResearchAgent
              ├─ ScriptAgent
              ├─ SEOAgent
              ├─ ThumbnailAgent
              └─ SocialAgent
                    └─► TemplateEngine (Jinja2 .md.j2 → Markdown)
                              └─► PackageWriter (writes .md files)
```

Agents produce **structured JSON only**. The `TemplateEngine` is the single responsible component for Markdown rendering.

## Running Tests

```bash
PYTHONPATH=. pytest -q
```

## Development Notes

- Keep provider implementations behind the `BaseProvider` abstraction.
- Agents must return structured JSON and never generate Markdown directly.
- Add new document types by adding a `.md.j2` template and registering it in `_DOCUMENT_TEMPLATES` inside `core/template_engine.py`.
- Use type hints and deterministic agent output for predictable templates.
