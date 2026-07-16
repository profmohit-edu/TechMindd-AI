"""REST API request and response schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class GenerateRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=500)
    workflow: str = Field(default="youtube_package", pattern=r"^[a-zA-Z0-9_-]+$")
    provider: str | None = Field(default=None, pattern=r"^(openai|gemini|auto)$")

    @field_validator("topic")
    @classmethod
    def sanitize_topic(cls, value: str) -> str:
        if any(ord(character) < 32 and character not in "\t\n\r" for character in value):
            raise ValueError("topic contains unsupported control characters")
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("topic cannot be empty")
        return cleaned


class GenerateResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    progress: int = Field(ge=0, le=100)
    current_stage: str
    provider: str
    workflow: str
    error: str | None = None
    topic: str
    logs: list[str] = Field(default_factory=list)


class KnowledgeResponse(BaseModel):
    filename: str | None = None
    status: str
    documents: int | None = None
    indexed_chunks: int | None = None


class OutputFile(BaseModel):
    name: str
    size: int
    download_url: str


class JobResultResponse(BaseModel):
    job_id: str
    package_metadata: dict[str, Any]
    output_files: list[OutputFile]
    download_urls: list[str]


class WorkflowResponse(BaseModel):
    name: str
    description: str
    provider: str
    plugins: list[str]
    validation: bool
    quality: bool
    reflection: bool
    parallel: bool
    output: str


class PluginResponse(BaseModel):
    name: str
    output_name: str
    prompt_template: str
    template: str


class ProviderResponse(BaseModel):
    name: str
    configured: bool
    priority: int | None
    health: str


class HealthResponse(BaseModel):
    status: str
    service: str
