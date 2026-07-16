from typing import Any
from agents.research_agent import ResearchAgent
from plugins.plugin import BasePlugin
from processors.research_processor import ResearchProcessor
from quality.research_scorer import ResearchScorer
from reflection.research_reflector import ResearchReflector
from validation.research_validator import ResearchValidator

class ResearchPlugin(BasePlugin):
    def name(self): return "research"
    def output_name(self): return "research.md"
    def prompt_template(self): return "prompts/research.txt"
    def schema(self): return {"type":"object","properties":{"topic":{"type":"string"},"audience":{"type":"string"},"summary":{"type":"string"},"insights":{"type":"array","items":{"type":"string"}}},"required":["topic","audience","summary","insights"]}
    def processor(self): return ResearchProcessor()
    def validator(self): return ResearchValidator()
    def scorer(self): return ResearchScorer()
    def reflector(self): return ResearchReflector()
    def template(self): return "research.jinja2"
    def order(self): return 10
    def create_agent(self, provider: Any, retriever: Any | None = None): return ResearchAgent(provider, retriever=retriever)
