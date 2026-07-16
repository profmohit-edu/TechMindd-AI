"""FastAPI application entry point."""

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
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
