import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routers import (
    auth,
    dashboard,
    interventions,
    meta,
    model,
    students,
    upload,
)

app = FastAPI(title="EduPredict API", version="0.1.0")
app.include_router(meta.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(model.router, prefix="/api")
app.include_router(students.router, prefix="/api")
app.include_router(interventions.router, prefix="/api")
app.include_router(upload.router, prefix="/api")

FRONTEND_DIST = Path(
    os.getenv(
        "FRONTEND_DIST",
        Path(__file__).resolve().parents[2] / "frontend" / "dist",
    )
).resolve()

RESERVED_PREFIXES = ("api", "docs", "redoc", "openapi.json")

if os.getenv("SERVE_FRONTEND") == "1" and FRONTEND_DIST.is_dir():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str) -> FileResponse:
        first_segment = full_path.split("/", 1)[0]
        if first_segment in RESERVED_PREFIXES:
            raise HTTPException(status_code=404, detail="Not Found")

        candidate = (FRONTEND_DIST / full_path).resolve()
        if (
            full_path
            and candidate.is_file()
            and FRONTEND_DIST in candidate.parents
        ):
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
