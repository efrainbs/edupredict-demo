from fastapi import FastAPI

from app.routers import meta

app = FastAPI(title="EduPredict API", version="0.1.0")
app.include_router(meta.router, prefix="/api")
