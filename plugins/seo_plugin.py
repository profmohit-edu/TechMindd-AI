from plugins.plugin import BasePlugin
from processors.seo_processor import SEOProcessor
from quality.seo_scorer import SEOScorer
from reflection.seo_reflector import SEOReflector
from validation.seo_validator import SEOValidator


class SEOPlugin(BasePlugin):
    def name(self):
        return "seo"

    def output_name(self):
        return "seo.md"

    def prompt_template(self):
        return "prompts/seo.txt"

    def schema(self):
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "keywords": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title", "description", "keywords"],
        }

    def processor(self):
        return SEOProcessor()

    def validator(self):
        return SEOValidator()

    def scorer(self):
        return SEOScorer()

    def reflector(self):
        return SEOReflector()

    def template(self):
        return "seo.jinja2"

    def order(self):
        return 30
