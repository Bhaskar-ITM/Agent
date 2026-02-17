from pathlib import Path

from fastapi import FastAPI

from app.api import projects, scans
from app.core.config import settings

app = FastAPI(title="DevSecOps Control Plane API")


@app.on_event("startup")
def validate_configuration():
    if not settings.DATABASE_URL:
        raise RuntimeError("DATABASE_URL is required")
    if not settings.JENKINS_BASE_URL:
        raise RuntimeError("JENKINS_BASE_URL is required")
    if not settings.STORAGE_PATH:
        raise RuntimeError("STORAGE_PATH is required")
    Path(settings.STORAGE_PATH).mkdir(parents=True, exist_ok=True)


app.include_router(projects.router, prefix="/api/v1", tags=["projects"])
app.include_router(scans.router, prefix="/api/v1", tags=["scans"])


@app.get("/")
def read_root():
    return {"message": "DevSecOps Control Plane is live"}
