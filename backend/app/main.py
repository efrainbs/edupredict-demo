from fastapi import FastAPI

from app.routers import auth, dashboard, interventions, meta, model, students

app = FastAPI(title="EduPredict API", version="0.1.0")
app.include_router(meta.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(model.router, prefix="/api")
app.include_router(students.router, prefix="/api")
app.include_router(interventions.router, prefix="/api")
