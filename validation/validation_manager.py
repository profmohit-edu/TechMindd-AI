"""Central validation manager for generated artifacts."""

from __future__ import annotations

import logging
from typing import Any, Protocol

from validation.research_validator import ResearchValidator
from validation.script_validator import ScriptValidator
from validation.seo_validator import SEOValidator
from validation.social_validator import SocialValidator
from validation.thumbnail_validator import ThumbnailValidator

LOGGER = logging.getLogger("techmindd.validation")


class Validator(Protocol):
    def validate(self, payload: Any) -> list[str]: ...


class ValidationError(ValueError):
    """Raised when a generated artifact does not satisfy production rules."""

    def __init__(self, artifact: str, errors: list[str]) -> None:
        self.artifact = artifact
        self.errors = tuple(errors)
        super().__init__(f"Validation failed for {artifact}: {'; '.join(errors)}")


class ValidationManager:
    """Select and execute the validator for each specialist artifact."""

    def __init__(self, validators: dict[str, Validator] | None = None) -> None:
        self._validators: dict[str, Validator] = validators or {
            "research": ResearchValidator(),
            "script": ScriptValidator(),
            "seo": SEOValidator(),
            "thumbnail": ThumbnailValidator(),
            "social": SocialValidator(),
        }

    def validate(self, artifact: str, payload: Any) -> None:
        validator = self._validators.get(artifact)
        if validator is None:
            errors = ["no validator registered"]
            LOGGER.error("Validation failed for %s: %s", artifact, errors[0])
            raise ValidationError(artifact, errors)

        errors = validator.validate(payload)
        if not isinstance(errors, list) or any(not isinstance(error, str) for error in errors):
            raise TypeError(f"Validator for {artifact} must return a list of errors")
        if errors:
            LOGGER.error("Validation failed for %s: %s", artifact, "; ".join(errors))
            raise ValidationError(artifact, errors)

        LOGGER.info("Validation passed for %s", artifact)
