from pathlib import Path
import sys

from fastapi import FastAPI

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Backend.app.routes.prediction import router
from Backend.app.routes.monitoring import router as monitoring_router

app = FastAPI(
    title="AI-Powered Predictive Maintenance"
)

app.include_router(router)
app.include_router(monitoring_router)

@app.get("/")
def root():
    return {
        "message": "Predictive Maintenance API Running"
    }