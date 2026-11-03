import pytest
from unittest.mock import MagicMock
from app.main import root
from app.api.health_router import liveness_probe, readiness_probe, dependency_health_check
from app.database import SessionLocal


def test_root_endpoint():
    data = root()
    assert "Project Sentinel" in data["message"]
    assert "environment" in data


def test_liveness_probe():
    data = liveness_probe()
    assert data["status"] == "alive"
    assert data["service"] == "Project Sentinel"
    assert "timestamp" in data


def test_readiness_probe():
    db = SessionLocal()
    try:
        mock_response = MagicMock()
        data = readiness_probe(response=mock_response, db=db)
        assert data["status"] == "ready"
        assert data["database"] == "connected"
    finally:
        db.close()


def test_dependencies_probe():
    db = SessionLocal()
    try:
        data = dependency_health_check(db=db)
        assert "dependencies" in data
        assert "database" in data["dependencies"]
        assert data["dependencies"]["database"]["status"] == "healthy"
        assert "redis" in data["dependencies"]
        assert "chromadb" in data["dependencies"]
        assert "llm_engine" in data["dependencies"]
    finally:
        db.close()
