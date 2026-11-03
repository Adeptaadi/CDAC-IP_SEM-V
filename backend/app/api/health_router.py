import time
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any

from app.database import get_db
from app.config import settings
from app.llm.client import llm_client
from app.knowledge.store import knowledge_store

health_router = APIRouter(tags=["System Health & Diagnostics"])


@health_router.get("/health")
@health_router.get("/health/live")
def liveness_probe():
    """Kubernetes/Container liveness probe to verify process responsiveness."""
    return {
        "status": "alive",
        "service": "Project Sentinel",
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time(),
    }


@health_router.get("/health/ready")
def readiness_probe(response: Response, db: Session = Depends(get_db)):
    """Kubernetes/Container readiness probe verifying operational database connectivity."""
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        db_ok = False

    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready", "reason": "database_unreachable"}

    return {
        "status": "ready",
        "database": "connected",
        "timestamp": time.time(),
    }


@health_router.get("/health/dependencies")
@health_router.get("/health/deps")
def dependency_health_check(db: Session = Depends(get_db)):
    """Inspects connectivity and responsiveness of all backing services (DB, Redis, ChromaDB, Ollama)."""
    results: Dict[str, Any] = {}

    # 1. Database Check
    t0 = time.time()
    try:
        db.execute(text("SELECT 1"))
        results["database"] = {
            "status": "healthy",
            "latency_ms": round((time.time() - t0) * 1000, 2),
            "engine": str(db.bind.dialect.name),
        }
    except Exception as e:
        results["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }

    # 2. Redis Check
    t0 = time.time()
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL, socket_timeout=0.5)
        ping_ok = r.ping()
        results["redis"] = {
            "status": "healthy" if ping_ok else "unresponsive",
            "latency_ms": round((time.time() - t0) * 1000, 2),
        }
    except Exception as e:
        results["redis"] = {
            "status": "offline",
            "mode": "standalone_in_memory_fallback",
            "info": str(e),
        }

    # 3. ChromaDB Check
    t0 = time.time()
    try:
        client = knowledge_store._get_client()
        is_fallback = (client == "in_memory_fallback")
        results["chromadb"] = {
            "status": "healthy",
            "mode": "in_memory_fallback" if is_fallback else "persistent_storage",
            "latency_ms": round((time.time() - t0) * 1000, 2),
        }
    except Exception as e:
        results["chromadb"] = {
            "status": "unhealthy",
            "error": str(e),
        }

    # 4. Ollama / LLM Check
    t0 = time.time()
    try:
        online = llm_client.is_available()
        results["llm_engine"] = {
            "status": "online" if online else "offline_fallback_mode",
            "provider": "ollama",
            "model": settings.PRIMARY_LLM_MODEL,
            "latency_ms": round((time.time() - t0) * 1000, 2),
        }
    except Exception as e:
        results["llm_engine"] = {
            "status": "offline_fallback_mode",
            "error": str(e),
        }

    overall_status = "healthy" if results["database"]["status"] == "healthy" else "degraded"

    return {
        "status": overall_status,
        "environment": settings.ENVIRONMENT,
        "dependencies": results,
    }
