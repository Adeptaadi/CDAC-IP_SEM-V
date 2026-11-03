"""Relational ORM Domain Models for Project Sentinel (14 Schema Domains).

Implements durable, stateful, auditable persistence compliant with
docs/DATABASE_SCHEMA_AND_PERSISTENCE_ARCHITECTURE_SPEC.md.
"""

from app.models.base import GUID, JSONB_TYPE, ARRAY_STRING, ARRAY_UUID
from app.models.identity import Role, User, UserRole
from app.models.dataset import Dataset, DatasetFile, ReplaySession, GroundTruthLabel
from app.models.telemetry import SecurityEvent
from app.models.detection import DetectionRule, ModelVersion, DetectionFinding
from app.models.correlation import Entity, EntityRelationship, IncidentCandidate
from app.models.investigation import (
    Investigation,
    InvestigationStateVersion,
    InvestigationEvent,
)
from app.models.orchestration import (
    Capability,
    CapabilityVersion,
    PlannerRun,
    PlannerDecision,
    WorkerExecution,
    AgentTask,
    TaskDependency,
    TaskAttempt,
    OrchestrationCheckpoint,
)
from app.models.evidence import (
    Evidence,
    TimelineEvent,
    Hypothesis,
    HypothesisEvidence,
)
from app.models.knowledge import (
    KnowledgeSource,
    KnowledgeDocument,
    KnowledgeChunk,
)
from app.models.response import (
    HumanReview,
    Recommendation,
    ResponseSimulation,
)
from app.models.reporting import Report, ReportSection
from app.models.audit import AuditLog
from app.models.evaluation import EvaluationRun, EvaluationResult

__all__ = [
    # Base Types
    "GUID",
    "JSONB_TYPE",
    "ARRAY_STRING",
    "ARRAY_UUID",
    # Domain 1: Identity
    "Role",
    "User",
    "UserRole",
    # Domain 2: Dataset
    "Dataset",
    "DatasetFile",
    "ReplaySession",
    "GroundTruthLabel",
    # Domain 3: Telemetry
    "SecurityEvent",
    # Domain 4: Detection
    "DetectionRule",
    "ModelVersion",
    "DetectionFinding",
    # Domain 5: Correlation
    "Entity",
    "EntityRelationship",
    "IncidentCandidate",
    # Domain 6: Investigation
    "Investigation",
    "InvestigationStateVersion",
    "InvestigationEvent",
    # Domain 7: Orchestration
    "Capability",
    "CapabilityVersion",
    "PlannerRun",
    "PlannerDecision",
    "WorkerExecution",
    "AgentTask",
    "TaskDependency",
    "TaskAttempt",
    "OrchestrationCheckpoint",
    # Domain 8: Evidence
    "Evidence",
    "TimelineEvent",
    "Hypothesis",
    "HypothesisEvidence",
    # Domain 9: Knowledge
    "KnowledgeSource",
    "KnowledgeDocument",
    "KnowledgeChunk",
    # Domain 10 & 11: Human Review & Response
    "HumanReview",
    "Recommendation",
    "ResponseSimulation",
    # Domain 12: Reporting
    "Report",
    "ReportSection",
    # Domain 13: Audit
    "AuditLog",
    # Domain 14: Evaluation
    "EvaluationRun",
    "EvaluationResult",
]
