from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.routers import crud, planner, views

app = FastAPI(
    title="ExamFlow API",
    description="Intelligent Examination Seating, Scheduling and Invigilator Management",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(crud.router)
app.include_router(planner.router)
app.include_router(views.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return {
        "product": "ExamFlow",
        "tagline": "Intelligent Exam Planner",
        "status": "running",
    }


@app.get("/api/health")
def health():
    return {"status": "healthy"}