# Plugin Architecture

TechMindd-AI loads extension points dynamically at runtime. New plugins are discovered automatically from package folders and selected via environment configuration.

## Discovery Rules

- Providers: `providers/*.py` classes inheriting `BaseProvider` with `provider_name`
- Agents: `agents/*.py` classes inheriting `BaseAgent` with `agent_name`
- Writers: `writers/*.py` classes inheriting `BaseWriterPlugin` with `writer_name`
- Exporters: `exporters/*.py` classes inheriting `BaseExporterPlugin` with `exporter_name`
- Retrievers: `rag/plugins/*.py` classes inheriting `BaseRetrieverPlugin` with `retriever_name`
- Template packs:
  - `templates/*.jinja2` => `default` pack
  - `templates/packs/<pack_name>/*.jinja2` => custom packs

No registry edits are required when adding a plugin module that follows the contract.

## Configuration Selection

Use `.env` values (or environment variables):

- `PROVIDER` (example: `openai`, `gemini`)
- `WRITER_PLUGIN` (`markdown`, `html`, `json`)
- `EXPORTER_PLUGIN` (`directory`, `zip`)
- `RETRIEVER_PLUGIN` (`chroma`)
- `TEMPLATE_PACK` (`default` or custom pack directory name)
- `DIRECTOR_AGENT` (default: `director`)
- `SPECIALIST_AGENTS` comma-separated order (default: `research,script,seo,thumbnail,social`)

Switching implementations is configuration-only.

## How to Add a Plugin

### Provider plugin

1. Add module under `providers/`
2. Subclass `BaseProvider`
3. Set `provider_name = "my_provider"`
4. Implement `generate_structured_json`
5. Set `PROVIDER=my_provider`

### Agent plugin

1. Add module under `agents/`
2. Subclass `BaseAgent`
3. Set `agent_name = "my_agent"`
4. Implement `generate(topic, director_plan=None)`
5. Add to `SPECIALIST_AGENTS` (or use as `DIRECTOR_AGENT`)

### Writer plugin

1. Add module under `writers/`
2. Subclass `BaseWriterPlugin`
3. Set `writer_name` and `file_extension`
4. Implement `transform(rendered_content, context)`
5. Set `WRITER_PLUGIN`

### Exporter plugin

1. Add module under `exporters/`
2. Subclass `BaseExporterPlugin`
3. Set `exporter_name`
4. Implement `export(package_dir, files_written)`
5. Set `EXPORTER_PLUGIN`

### Retriever plugin

1. Add module under `rag/plugins/`
2. Subclass `BaseRetrieverPlugin`
3. Set `retriever_name`
4. Implement `build() -> Retriever | None`
5. Set `RETRIEVER_PLUGIN`

### Template pack

1. Create directory `templates/packs/<pack_name>/`
2. Add `research.jinja2`, `script.jinja2`, `seo.jinja2`, `thumbnail.jinja2`, `social.jinja2` (and optional extra templates)
3. Set `TEMPLATE_PACK=<pack_name>`

