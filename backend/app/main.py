from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.api.routers import router
from app.api.dataset_router import dataset_router

# Initialize tables if not using Alembic migrations in dev
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Project Sentinel API",
    description="Agentic AI-powered Autonomous Cyber Threat Hunting Platform Gateway",
    version="1.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(dataset_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to Project Sentinel Autonomous Cyber Threat Hunting Platform",
        "docs_url": "/docs",
        "environment": settings.ENVIRONMENT
    }
