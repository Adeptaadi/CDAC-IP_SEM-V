from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.api.routers import router
from app.api.dataset_router import dataset_router
from app.api.knowledge_router import knowledge_router
from app.api.worker_router import worker_router
from app.api.planner_router import planner_router
from app.api.ws import ws_manager

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
app.include_router(knowledge_router)
app.include_router(worker_router)
app.include_router(planner_router)


@app.websocket("/ws/investigations/{investigation_id}")
async def websocket_investigation_endpoint(websocket: WebSocket, investigation_id: str):
    await ws_manager.connect(websocket, investigation_id)
    try:
        while True:
            # Keep connection alive receiving ping/messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, investigation_id)


@app.get("/")
def root():
    return {
        "message": "Welcome to Project Sentinel Autonomous Cyber Threat Hunting Platform",
        "docs_url": "/docs",
        "environment": settings.ENVIRONMENT
    }
