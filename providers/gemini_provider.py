"""Gemini provider implementation.

This module provides a typed wrapper around the official google-genai SDK
for issuing model requests and returning structured JSON output with usage
accounting when available.
"""

from __future__ import annotations

import json
import logging
import random
import time
from typing import Any, Dict, Optional

from google import genai
from google.genai import types

from config import settings

logger = logging.getLogger(__name__)

_MAX_RETRIES: int = 4
_INITIAL_BACKOFF_SECONDS: float = 0.5
_MAX_BACKOFF_SECONDS: float = 8.0
_REQUEST_TIMEOUT_SECONDS: float = 30.0
_DEFAULT_GEMINI_MODEL: str = "gemini-2.5-flash"


class GeminiProviderError(Exception):
    """Base exception raised for Gemini provider failures."""


class GeminiProviderConfigurationError(GeminiProviderError):
    """Raised when required Gemini configuration is missing or invalid."""


class GeminiProviderRequestError(GeminiProviderError):
    """Raised when a Gemini request fails after retries or due to non-retryable errors."""


class GeminiProvider:
    """Typed Gemini provider using the official google-genai Python SDK."""

    def __init__(self, *, timeout_seconds: float = _REQUEST_TIMEOUT_SECONDS) -> None:
        self.timeout_seconds = timeout_seconds
        self._ensure_config()
        self.client = genai.Client(api_key=settings.gemini_api_key)
        configured_model = getattr(settings, "gemini_model", "")
        self.model = str(configured_model).strip() or _DEFAULT_GEMINI_MODEL
        self.max_retries = _MAX_RETRIES
        self.last_usage: Dict[str, int] = {}

    @staticmethod
    def _ensure_config() -> None:
        if not settings.gemini_api_key or not str(settings.gemini_api_key).strip():
            raise GeminiProviderConfigurationError(
                "settings.gemini_api_key is required but not configured."
            )

    @staticmethod
    def _extract_usage(response: Any) -> Dict[str, int]:
        usage = getattr(response, "usage_metadata", None)

        input_tokens = int(getattr(usage, "prompt_token_count", 0) or 0)
        output_tokens = int(getattr(usage, "candidates_token_count", 0) or 0)
        total_tokens = int(getattr(usage, "total_token_count", input_tokens + output_tokens) or 0)

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
        }

    @staticmethod
    def _extract_content(response: Any) -> str:
        text = getattr(response, "text", None)
        if text is not None and str(text).strip():
            return str(text)

        candidates = getattr(response, "candidates", None) or []
        if candidates:
            candidate = candidates[0]
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", None) or []
            for part in parts:
                part_text = getattr(part, "text", None)
                if part_text is not None and str(part_text).strip():
                    return str(part_text)

        raise GeminiProviderRequestError("Gemini response missing text content.")

    @staticmethod
    def _parse_json_output(text: str) -> Dict[str, Any]:
        try:
            parsed: Any = json.loads(text)
        except json.JSONDecodeError as exc:
            raise GeminiProviderRequestError("Model output was not valid JSON.") from exc

        if not isinstance(parsed, dict):
            raise GeminiProviderRequestError("Model output JSON must be an object.")

        if not parsed:
            raise GeminiProviderRequestError("Model output JSON was empty.")

        return parsed

    @staticmethod
    def _compute_backoff(attempt: int) -> float:
        base = min(_INITIAL_BACKOFF_SECONDS * (2**attempt), _MAX_BACKOFF_SECONDS)
        jitter = random.uniform(0.0, 0.25 * base)  # noqa: S311 - retry jitter
        return base + jitter

    def generate_structured_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: Dict[str, Any],
        temperature: float = 0.0,
        max_output_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.info(
                    "Sending Gemini request",
                    extra={
                        "model": self.model,
                        "attempt": attempt + 1,
                        "max_attempts": self.max_retries + 1,
                    },
                )

                config_kwargs: Dict[str, Any] = {
                    "system_instruction": system_prompt,
                    "response_mime_type": "application/json",
                    "temperature": temperature,
                }
                if response_schema:
                    config_kwargs["response_schema"] = response_schema

                generation_config = types.GenerateContentConfig(**config_kwargs)

                if max_output_tokens is not None:
                    generation_config.max_output_tokens = max_output_tokens

                started_at = time.monotonic()
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=user_prompt,
                    config=generation_config,
                )
                elapsed = time.monotonic() - started_at
                if elapsed > self.timeout_seconds:
                    raise TimeoutError(
                        f"Gemini request exceeded timeout of {self.timeout_seconds:.2f}s (elapsed {elapsed:.2f}s)."
                    )

                content = self._extract_content(response)
                data = self._parse_json_output(content)
                usage = self._extract_usage(response)

                logger.info("Gemini request succeeded", extra={"model": self.model, "usage": usage})

                self.last_usage = usage
                logger.debug("Gemini returned structured JSON with %d fields", len(data))
                return data

            except GeminiProviderError:
                raise

            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt >= self.max_retries:
                    logger.error(
                        "Gemini request failed after retries",
                        extra={"error": str(exc), "attempts": attempt + 1},
                    )
                    break

                sleep_seconds = self._compute_backoff(attempt)
                logger.warning(
                    "Gemini error; retrying with backoff",
                    extra={
                        "error": str(exc),
                        "sleep_seconds": sleep_seconds,
                        "attempt": attempt + 1,
                    },
                )
                time.sleep(sleep_seconds)

        raise GeminiProviderRequestError(
            "Gemini request failed after retries due to transient errors."
        ) from last_error
