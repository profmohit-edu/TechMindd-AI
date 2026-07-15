"""OpenAI provider implementation.

This module provides a thin, typed wrapper around the latest OpenAI Python SDK
for issuing a single model request and returning structured JSON output with
usage accounting.
"""

from __future__ import annotations

import json
import logging
import random
import time
from typing import Any, Dict, Optional

from openai import APIConnectionError, APITimeoutError, BadRequestError, OpenAI, RateLimitError

from config import settings

logger = logging.getLogger(__name__)

_MAX_RETRIES: int = 4
_INITIAL_BACKOFF_SECONDS: float = 0.5
_MAX_BACKOFF_SECONDS: float = 8.0
_REQUEST_TIMEOUT_SECONDS: float = 30.0


class OpenAIProviderError(Exception):
    """Base exception raised for OpenAI provider failures."""


class OpenAIProviderConfigurationError(OpenAIProviderError):
    """Raised when required OpenAI configuration is missing or invalid."""


class OpenAIProviderRequestError(OpenAIProviderError):
    """Raised when an OpenAI request fails after retries or due to non-retryable errors."""


class OpenAIProvider:
    """Typed OpenAI provider using the latest OpenAI Python SDK.

    The provider issues exactly one OpenAI API request per attempt and returns
    structured JSON with token usage metrics.
    """

    def __init__(self, *, timeout_seconds: float = _REQUEST_TIMEOUT_SECONDS) -> None:
        """Initialize provider.

        Args:
            timeout_seconds: Per-request timeout in seconds.

        Raises:
            OpenAIProviderConfigurationError: If required configuration is missing.
        """
        self.timeout_seconds = timeout_seconds
        self._ensure_config()
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = str(settings.openai_model)

    @staticmethod
    def _ensure_config() -> None:
        """Validate required OpenAI configuration values.

        Raises:
            OpenAIProviderConfigurationError: If `settings.openai_api_key` or
                `settings.openai_model` is missing.
        """
        if not settings.openai_api_key or not str(settings.openai_api_key).strip():
            raise OpenAIProviderConfigurationError("settings.openai_api_key is required but not configured.")
        if not settings.openai_model or not str(settings.openai_model).strip():
            raise OpenAIProviderConfigurationError("settings.openai_model is required but not configured.")

    @staticmethod
    def _extract_usage(response: Any) -> Dict[str, int]:
        """Extract token usage counters from an OpenAI SDK response.

        Args:
            response: SDK response object from chat/completions.

        Returns:
            dict[str, int]: input_tokens, output_tokens, total_tokens.
        """
        usage = getattr(response, "usage", None)

        input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        total_tokens = int(getattr(usage, "total_tokens", input_tokens + output_tokens) or 0)

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
        }

    @staticmethod
    def _extract_content(response: Any) -> str:
        """Extract assistant text content from a chat completion response.

        Args:
            response: SDK response object.

        Returns:
            str: Assistant content text.

        Raises:
            OpenAIProviderRequestError: If response content is missing.
        """
        choices = getattr(response, "choices", None)
        if not choices:
            raise OpenAIProviderRequestError("OpenAI response did not include any choices.")

        message = choices[0].message
        content = getattr(message, "content", None)
        if content is None or not str(content).strip():
            raise OpenAIProviderRequestError("OpenAI response choice missing message content.")

        return str(content)

    @staticmethod
    def _parse_json_output(text: str) -> Dict[str, Any]:
        """Parse model text output as a JSON object.

        Args:
            text: Raw model output text.

        Returns:
            dict[str, Any]: Parsed JSON object.

        Raises:
            OpenAIProviderRequestError: If output is not valid JSON object.
        """
        try:
            parsed: Any = json.loads(text)
        except json.JSONDecodeError as exc:
            raise OpenAIProviderRequestError("Model output was not valid JSON.") from exc

        if not isinstance(parsed, dict):
            raise OpenAIProviderRequestError("Model output JSON must be an object.")

        return parsed

    @staticmethod
    def _compute_backoff(attempt: int) -> float:
        """Compute exponential backoff with jitter.

        Args:
            attempt: Zero-based retry attempt index.

        Returns:
            float: Sleep duration in seconds.
        """
        base = min(_INITIAL_BACKOFF_SECONDS * (2**attempt), _MAX_BACKOFF_SECONDS)
        jitter = random.uniform(0.0, 0.25 * base)
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
        """Perform one logical OpenAI request flow and return structured JSON.

        Retries transient failures using exponential backoff. Each attempt performs
        exactly one OpenAI API request.

        Args:
            system_prompt: System instruction text.
            user_prompt: User input text.
            response_schema: JSON schema object for structured output.
            temperature: Sampling temperature.
            max_output_tokens: Optional max completion token limit.

        Returns:
            dict[str, Any]:
                {
                    "data": <parsed json object>,
                    "usage": {
                        "input_tokens": int,
                        "output_tokens": int,
                        "total_tokens": int
                    },
                    "model": str
                }

        Raises:
            OpenAIProviderRequestError: On request failure or invalid response payload.
        """
        last_error: Optional[Exception] = None

        for attempt in range(_MAX_RETRIES + 1):
            try:
                logger.info(
                    "Sending OpenAI request",
                    extra={"model": self.model, "attempt": attempt + 1, "max_attempts": _MAX_RETRIES + 1},
                )

                request_kwargs: Dict[str, Any] = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": temperature,
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "structured_response",
                            "schema": response_schema,
                            "strict": True,
                        },
                    },
                    "timeout": self.timeout_seconds,
                }

                if max_output_tokens is not None:
                    request_kwargs["max_completion_tokens"] = max_output_tokens

                response = self.client.chat.completions.create(**request_kwargs)

                content = self._extract_content(response)
                data = self._parse_json_output(content)
                usage = self._extract_usage(response)

                logger.info("OpenAI request succeeded", extra={"model": self.model, "usage": usage})

                return {
                    "data": data,
                    "usage": usage,
                    "model": self.model,
                }

            except (RateLimitError, APITimeoutError, APIConnectionError) as exc:
                last_error = exc
                if attempt >= _MAX_RETRIES:
                    logger.error(
                        "OpenAI transient failure after retries",
                        extra={"error": str(exc), "attempts": attempt + 1},
                    )
                    break

                sleep_seconds = self._compute_backoff(attempt)
                logger.warning(
                    "Transient OpenAI error; retrying with backoff",
                    extra={"error": str(exc), "sleep_seconds": sleep_seconds, "attempt": attempt + 1},
                )
                time.sleep(sleep_seconds)

            except BadRequestError as exc:
                logger.error("OpenAI bad request", extra={"error": str(exc)})
                raise OpenAIProviderRequestError(
                    "OpenAI rejected the request. Check prompts and response schema."
                ) from exc

            except OpenAIProviderError:
                raise

            except Exception as exc:  # noqa: BLE001
                logger.exception("Unexpected error during OpenAI request")
                raise OpenAIProviderRequestError("Unexpected error while calling OpenAI.") from exc

        raise OpenAIProviderRequestError(
            "OpenAI request failed after retries due to transient errors."
        ) from last_error
