from plugins.plugin import BasePlugin
from processors.thumbnail_processor import ThumbnailProcessor
from quality.thumbnail_scorer import ThumbnailScorer
from reflection.thumbnail_reflector import ThumbnailReflector
from validation.thumbnail_validator import ThumbnailValidator

class ThumbnailPlugin(BasePlugin):
    def name(self): return "thumbnail"
    def output_name(self): return "thumbnail.md"
    def prompt_template(self): return "prompts/thumbnail.txt"
    def schema(self): return {"type":"object","properties":{"headline":{"type":"string"},"subheadline":{"type":"string"},"visual_notes":{"type":"string"}},"required":["headline","subheadline","visual_notes"]}
    def processor(self): return ThumbnailProcessor()
    def validator(self): return ThumbnailValidator()
    def scorer(self): return ThumbnailScorer()
    def reflector(self): return ThumbnailReflector()
    def template(self): return "thumbnail.jinja2"
    def order(self): return 40
