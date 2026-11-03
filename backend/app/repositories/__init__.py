"""Durable Repository Layer for Project Sentinel (Phase 2).

Provides encapsulated, testable database access with transaction boundaries,
optimistic concurrency control, and state versioning.
"""

from app.repositories.base import BaseRepository
from app.repositories.investigation_repo import InvestigationRepository, OptimisticLockError
from app.repositories.event_repo import SecurityEventRepository
from app.repositories.dataset_repo import DatasetRepository
from app.repositories.task_repo import TaskRepository
from app.repositories.evidence_repo import EvidenceRepository

__all__ = [
    "BaseRepository",
    "InvestigationRepository",
    "OptimisticLockError",
    "SecurityEventRepository",
    "DatasetRepository",
    "TaskRepository",
    "EvidenceRepository",
]
