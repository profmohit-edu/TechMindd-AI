"""FastAPI application entry point."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from api.dependencies import get_job_service
from api.middleware import ProductionMiddleware
from api.routes import router
from core.version import VERSION
from observability import configure_logging
from observability.metrics import HEALTH

configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    HEALTH.set(1)
    yield
    HEALTH.set(0)
    get_job_service().shutdown()


app = FastAPI(
    title="TechMindd-AI API",
    description="Workflow-driven AI content package generation service.",
    version=VERSION,
    root_path=os.getenv("ROOT_PATH", "").rstrip("/"),
    lifespan=lifespan,
)
app.include_router(router)
app.add_middleware(ProductionMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


frontend_dist = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if frontend_dist.is_dir():
    assets_dir = frontend_dist / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @app.get("/{frontend_path:path}", include_in_schema=False)
    async def frontend(frontend_path: str) -> FileResponse:
        """Serve the React application and its client-side routes."""
        candidate = (frontend_dist / frontend_path).resolve()
        if candidate.is_file() and frontend_dist in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(frontend_dist / "index.html")
