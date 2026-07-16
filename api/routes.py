"""FastAPI route definitions."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse

from api.dependencies import JobService, get_job_service, provider_health
from api.schemas import (
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
    JobResultResponse,
    JobStatusResponse,
    OutputFile,
    PluginResponse,
    ProviderResponse,
    WorkflowResponse,
)
from plugins import PluginManager
from workflows import WorkflowEngine


router = APIRouter()


@router.post(
    "/generate",
    response_model=GenerateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def generate(
    payload: GenerateRequest,
    jobs: JobService = Depends(get_job_service),
) -> GenerateResponse:
    try:
        job = jobs.create(payload.topic, payload.workflow)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return GenerateResponse(job_id=job.job_id, status=job.status)


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def job_status(
    job_id: str,
    jobs: JobService = Depends(get_job_service),
) -> JobStatusResponse:
    try:
        job = jobs.get(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    return JobStatusResponse(**job.__dict__)


@router.get("/jobs/{job_id}/result", response_model=JobResultResponse)
def job_result(
    job_id: str,
    request: Request,
    jobs: JobService = Depends(get_job_service),
) -> JobResultResponse:
    try:
        package_dir = jobs.package_dir(job_id)
        metadata = jobs.metadata(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=f"Job is {exc}") from exc

    output_files: list[OutputFile] = []
    for path in sorted(package_dir.iterdir()):
        if not path.is_file():
            continue
        url = str(
            request.url_for("download_job_file", job_id=job_id, filename=path.name)
        )
        output_files.append(
            OutputFile(name=path.name, size=path.stat().st_size, download_url=url)
        )
    return JobResultResponse(
        job_id=job_id,
        package_metadata=metadata,
        output_files=output_files,
        download_urls=[item.download_url for item in output_files],
    )


@router.get("/jobs/{job_id}/files/{filename:path}", name="download_job_file")
def download_job_file(
    job_id: str,
    filename: str,
    jobs: JobService = Depends(get_job_service),
) -> FileResponse:
    try:
        package_dir = jobs.package_dir(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=f"Job is {exc}") from exc
    target = (package_dir / filename).resolve()
    if target.parent != package_dir or not target.is_file():
        raise HTTPException(status_code=404, detail="Output file not found")
    return FileResponse(target, filename=target.name)


@router.get("/workflows", response_model=list[WorkflowResponse])
def workflows() -> list[WorkflowResponse]:
    engine = WorkflowEngine()
    return [
        WorkflowResponse(**engine.load(path.stem).__dict__)
        for path in sorted(engine.loader.workflows_dir.glob("*.yaml"))
    ]


@router.get("/plugins", response_model=list[PluginResponse])
def plugins() -> list[PluginResponse]:
    return [
        PluginResponse(
            name=plugin.name(),
            output_name=plugin.output_name(),
            prompt_template=plugin.prompt_template(),
            template=plugin.template(),
        )
        for plugin in PluginManager().discover().all()
    ]


@router.get("/providers", response_model=list[ProviderResponse])
def providers() -> list[ProviderResponse]:
    return [ProviderResponse(**item) for item in provider_health()]


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="healthy", service="TechMindd-AI")
