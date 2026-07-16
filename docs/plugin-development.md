# Plugin developer guide

A plugin adds a content artifact without factory changes. Create one Python module in `plugins/`, one prompt in `prompts/`, and one Jinja template in `templates/`. The registry discovers concrete `BasePlugin` subclasses automatically.

```python
from plugins.plugin import BasePlugin


class ExamplePlugin(BasePlugin):
    def name(self): return "example"
    def output_name(self): return "example.md"
    def prompt_template(self): return "example.txt"
    def schema(self): return {"summary": str}
    def processor(self): return ExampleProcessor
    def validator(self): return ExampleValidator
    def scorer(self): return ExampleScorer
    def reflector(self): return ExampleReflector
    def template(self): return "example.md.j2"
```

Names must be unique, stable, lowercase workflow identifiers. Output names must be safe relative filenames. Keep processors deterministic, validators structural, and scorers bounded from 0–100. Reflectors receive the artifact, Director plan, quality score, and validation result; regeneration feedback should be specific and must preserve the declared schema.

Add the plugin name to a workflow YAML's `plugins` list. Test discovery, schema failure, quality thresholds, rendering, and package inclusion. Never put provider calls in validators, scorers, templates, or import-time module code; generation belongs in the agent/provider path so failover, budgets, and metrics remain effective.

Compatibility is part of the public contract: do not rename an output or remove schema fields in a patch/minor release. Use a new plugin name or a major version for incompatible artifact changes.
