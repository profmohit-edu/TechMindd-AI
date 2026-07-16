"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.dependencies import get_job_service
from api.routes import router


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    get_job_service().shutdown()


app = FastAPI(
    title="TechMindd-AI API",
    description="Workflow-driven AI content package generation service.",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
