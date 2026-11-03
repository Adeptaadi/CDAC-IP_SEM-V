import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import engine, Base
from app.api.health_router import health_router
from app.api.routers import router
from app.api.dataset_router import dataset_router
from app.api.knowledge_router import knowledge_router
from app.api.worker_router import worker_router
from app.api.planner_router import planner_router
from app.api.eval_router import eval_router
from app.api.ws import ws_manager

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sentinel")

# Initialize tables if not using Alembic migrations in dev
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Project Sentinel API",
    description="Agentic AI-powered Autonomous Cyber Threat Hunting Platform Gateway",
    version="1.0.0"
)

# Global Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error on %s %s: %s", request.method, request.url.path, exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "message": "Invalid request payload format"}
    )

@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error("Database query failed on %s %s: %s", request.method, request.url.path, str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "An internal database error occurred while processing the request."}
    )

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(router)
from app.api.dataset_router import dataset_router
from app.api.knowledge_router import knowledge_router
from app.api.worker_router import worker_router
from app.api.planner_router import planner_router
from app.api.eval_router import eval_router
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
app.include_router(eval_router)


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
