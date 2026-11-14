"""ClimateLens entry point. Run: python -m uvicorn app.main:app"""
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

from .investigations import router as investigations_router
from .tutor import router as tutor_router
from .reports import router as reports_router

ROOT = Path(__file__).parent
app = FastAPI(title="ClimateLens", version="0.2.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
app.include_router(investigations_router)
app.include_router(tutor_router)
app.include_router(reports_router)

@app.get("/")
def index():
    return FileResponse(ROOT / "static/index.html")

@app.get("/api/health")
def health():
    return {"status": "ok", "version": app.version}
