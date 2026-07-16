from plugins.plugin import BasePlugin
from processors.social_processor import SocialProcessor
from quality.social_scorer import SocialScorer
from reflection.social_reflector import SocialReflector
from validation.social_validator import SocialValidator


class SocialPlugin(BasePlugin):
    def name(self):
        return "social"

    def output_name(self):
        return "social.md"

    def prompt_template(self):
        return "prompts/social.txt"

    def schema(self):
        return {
            "type": "object",
            "properties": {
                "caption": {"type": "string"},
                "hashtags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["caption", "hashtags"],
        }

    def processor(self):
        return SocialProcessor()

    def validator(self):
        return SocialValidator()

    def scorer(self):
        return SocialScorer()

    def reflector(self):
        return SocialReflector()

    def template(self):
        return "social.jinja2"

    def order(self):
        return 50
