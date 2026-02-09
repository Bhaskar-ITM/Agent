from fastapi import FastAPI
from app.api import projects, scans

app = FastAPI(title="DevSecOps Control Plane API")

app.include_router(projects.router, prefix="/api", tags=["projects"])
app.include_router(scans.router, prefix="/api", tags=["scans"])

@app.get("/")
def read_root():
    return {"message": "DevSecOps Control Plane is live"}
