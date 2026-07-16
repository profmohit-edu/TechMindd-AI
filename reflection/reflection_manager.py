"""Reflection coordination and report generation."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from quality import ArtifactQuality
from reflection.research_reflector import ResearchReflector
from reflection.script_reflector import ScriptReflector
from reflection.seo_reflector import SEOReflector
from reflection.social_reflector import SocialReflector
from reflection.thumbnail_reflector import ThumbnailReflector


LOGGER = logging.getLogger("techmindd.reflection")


class Reflector(Protocol):
    def reflect(
        self,
        original: dict[str, Any],
        director_plan: dict[str, Any],
        quality_score: dict[str, Any],
        validation_results: dict[str, Any],
    ) -> dict[str, str]: ...


@dataclass(frozen=True)
class ReflectionDecision:
    artifact: str
    decision: str
    feedback: str
    before_score: float


class ReflectionManager:
    """Run artifact reflectors and produce deterministic reflection reports."""

    def __init__(self, reflectors: dict[str, Reflector] | None = None) -> None:
        self._reflectors: dict[str, Reflector] = reflectors or {
            "research": ResearchReflector(),
            "script": ScriptReflector(),
            "seo": SEOReflector(),
            "thumbnail": ThumbnailReflector(),
            "social": SocialReflector(),
        }

    def reflect(
        self,
        artifact: str,
        original: dict[str, Any],
        director_plan: dict[str, Any],
        quality: ArtifactQuality,
        validation_results: dict[str, Any],
    ) -> ReflectionDecision:
        reflector = self._reflectors.get(artifact)
        if reflector is None:
            raise KeyError(f"No reflector registered for {artifact}")
        quality_score = {
            "overall": quality.score,
            "criteria": dict(quality.criteria),
            "recommendations": list(quality.recommendations),
        }
        result = reflector.reflect(
            original,
            director_plan,
            quality_score,
            validation_results,
        )
        decision = ReflectionDecision(
            artifact=artifact,
            decision=result["decision"],
            feedback=result["feedback"],
            before_score=quality.score,
        )
        LOGGER.info(
            "Reflection completed for %s: decision=%s score=%.2f feedback=%s",
            artifact,
            decision.decision,
            decision.before_score,
            decision.feedback,
        )
        return decision

    def build_report(
        self,
        decisions: dict[str, ReflectionDecision],
        final_scores: dict[str, ArtifactQuality],
        regenerated_artifacts: list[str],
    ) -> dict[str, Any]:
        ordered = [name for name in self._reflectors if name in decisions]
        regenerated = [name for name in ordered if name in regenerated_artifacts]
        accepted = [name for name in ordered if name not in regenerated_artifacts]
        return {
            "accepted_artifacts": accepted,
            "regenerated_artifacts": regenerated,
            "improvement_reasons": {
                name: decisions[name].feedback
                for name in ordered
                if decisions[name].decision == "improved"
            },
            "before_score": {name: decisions[name].before_score for name in ordered},
            "after_score": {name: final_scores[name].score for name in ordered},
        }

    def write_report(
        self,
        package_dir: Path,
        decisions: dict[str, ReflectionDecision],
        final_scores: dict[str, ArtifactQuality],
        regenerated_artifacts: list[str],
    ) -> tuple[Path, dict[str, Any]]:
        report = self.build_report(decisions, final_scores, regenerated_artifacts)
        path = package_dir / "reflection_report.json"
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return path, report
