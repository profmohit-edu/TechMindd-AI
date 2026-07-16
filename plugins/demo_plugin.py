from plugins.plugin import BasePlugin


class DemoProcessor:
    def process(self, payload):
        return dict(payload)


class DemoValidator:
    def validate(self, payload):
        return [
            f"{key} must be non-empty"
            for key in ("title", "body")
            if not isinstance(payload.get(key), str) or not payload[key].strip()
        ]


class DemoScorer:
    def score(self, payload):
        return {
            "completeness": 100.0,
            "readability": 90.0 if len(payload.get("body", "").split()) >= 3 else 70.0,
        }


class DemoReflector:
    def reflect(self, original, director_plan, quality_score, validation_results):
        _ = original, director_plan, validation_results
        weak = [key for key, value in quality_score["criteria"].items() if value < 70]
        return (
            {"decision": "improved", "feedback": "Improve demo " + ", ".join(weak)}
            if weak
            else {"decision": "accepted", "feedback": "Demo meets quality criteria"}
        )


class DemoPlugin(BasePlugin):
    def name(self):
        return "demo"

    def output_name(self):
        return "demo.md"

    def prompt_template(self):
        return "prompts/demo.txt"

    def schema(self):
        return {
            "type": "object",
            "properties": {"title": {"type": "string"}, "body": {"type": "string"}},
            "required": ["title", "body"],
        }

    def processor(self):
        return DemoProcessor()

    def validator(self):
        return DemoValidator()

    def scorer(self):
        return DemoScorer()

    def reflector(self):
        return DemoReflector()

    def template(self):
        return "demo.jinja2"

    def order(self):
        return 60
