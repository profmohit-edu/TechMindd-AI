from plugins.plugin import BasePlugin
from processors.script_processor import ScriptProcessor
from quality.script_scorer import ScriptScorer
from reflection.script_reflector import ScriptReflector
from validation.script_validator import ScriptValidator

class ScriptPlugin(BasePlugin):
    def name(self): return "script"
    def output_name(self): return "script.md"
    def prompt_template(self): return "prompts/script.txt"
    def schema(self): return {"type":"object","properties":{"title":{"type":"string"},"hook":{"type":"string"},"sections":{"type":"array","items":{"type":"string"}}},"required":["title","hook","sections"]}
    def processor(self): return ScriptProcessor()
    def validator(self): return ScriptValidator()
    def scorer(self): return ScriptScorer()
    def reflector(self): return ScriptReflector()
    def template(self): return "script.jinja2"
    def order(self): return 20
