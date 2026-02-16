from fastapi import FastAPI
from app.api import projects, scans
import threading
import time
from app.services.scan_monitor import monitor_scans

app = FastAPI(title="DevSecOps Control Plane API")

def run_monitor():
    while True:
        try:
            # Poll every 5 seconds for simulation (spec says 15-30s, but faster is better for dev/tests)
            monitor_scans(scans.scans_db)
        except Exception as e:
            print(f"Monitor error: {e}")
        time.sleep(5)

@app.on_event("startup")
def startup_event():
    thread = threading.Thread(target=run_monitor, daemon=True)
    thread.start()

app.include_router(projects.router, prefix="/api/v1", tags=["projects"])
app.include_router(scans.router, prefix="/api/v1", tags=["scans"])

@app.get("/")
def read_root():
    return {"message": "DevSecOps Control Plane is live"}
