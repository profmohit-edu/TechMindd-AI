"""Quality scoring coordination and report generation."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from quality.research_scorer import ResearchScorer
from quality.script_scorer import ScriptScorer
from quality.seo_scorer import SEOScorer
from quality.social_scorer import SocialScorer
from quality.thumbnail_scorer import ThumbnailScorer

LOGGER = logging.getLogger("techmindd.quality")


class Scorer(Protocol):
    def score(self, payload: dict[str, Any]) -> dict[str, float]: ...


@dataclass(frozen=True)
class ArtifactQuality:
    artifact: str
    score: float
    criteria: dict[str, float]
    recommendations: tuple[str, ...]


class QualityError(RuntimeError):
    """Raised when an artifact remains below the quality threshold."""

    def __init__(self, result: ArtifactQuality, threshold: float) -> None:
        self.artifact = result.artifact
        self.score = result.score
        self.threshold = threshold
        super().__init__(
            f"Quality score for {result.artifact} is {result.score:.2f}; minimum is {threshold:.2f}"
        )


class QualityManager:
    """Score specialist artifacts and build package-level QA reports."""

    def __init__(self, threshold: float = 70.0, scorers: dict[str, Scorer] | None = None) -> None:
        if not 0 <= threshold <= 100:
            raise ValueError("quality threshold must be between 0 and 100")
        self.threshold = threshold
        self._scorers: dict[str, Scorer] = scorers or {
            "research": ResearchScorer(),
            "script": ScriptScorer(),
            "seo": SEOScorer(),
            "thumbnail": ThumbnailScorer(),
            "social": SocialScorer(),
        }

    def score(self, artifact: str, payload: dict[str, Any]) -> ArtifactQuality:
        scorer = self._scorers.get(artifact)
        if scorer is None:
            raise KeyError(f"No quality scorer registered for {artifact}")
        criteria = scorer.score(payload)
        if not isinstance(criteria, dict) or not criteria:
            raise ValueError(f"Quality scorer for {artifact} returned no criteria")
        if any(
            not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 100
            for value in criteria.values()
        ):
            raise ValueError(f"Quality scorer for {artifact} returned an invalid score")
        score = round(sum(criteria.values()) / len(criteria), 2)
        recommendations = tuple(
            f"Improve {artifact} {criterion.replace('_', ' ')}"
            for criterion, criterion_score in criteria.items()
            if criterion_score < self.threshold
        )
        result = ArtifactQuality(artifact, score, criteria, recommendations)
        LOGGER.info(
            "Quality scored for %s: score=%.2f criteria=%s",
            artifact,
            score,
            criteria,
        )
        return result

    def require_quality(self, result: ArtifactQuality) -> None:
        if result.score < self.threshold:
            LOGGER.error(
                "Quality failed for %s: score=%.2f threshold=%.2f",
                result.artifact,
                result.score,
                self.threshold,
            )
            raise QualityError(result, self.threshold)
        LOGGER.info("Quality passed for %s: score=%.2f", result.artifact, result.score)

    def build_report(self, results: dict[str, ArtifactQuality]) -> dict[str, Any]:
        if not results:
            raise ValueError("quality report requires at least one artifact score")
        ordered_results = [results[name] for name in self._scorers if name in results]
        artifact_scores = {result.artifact: result.score for result in ordered_results}
        recommendations = [
            recommendation
            for result in ordered_results
            for recommendation in result.recommendations
        ]
        return {
            "overall_score": round(sum(artifact_scores.values()) / len(artifact_scores), 2),
            "artifact_scores": artifact_scores,
            "recommendations": recommendations,
        }

    def write_report(
        self,
        package_dir: Path,
        results: dict[str, ArtifactQuality],
    ) -> tuple[Path, dict[str, Any]]:
        report = self.build_report(results)
        path = package_dir / "quality_report.json"
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return path, report
