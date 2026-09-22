from typing import Dict, Type
from app.workers.base import BaseWorker
from app.workers.detection_worker import DetectionWorker
from app.workers.correlation_worker import CorrelationWorker
from app.workers.investigation_worker import InvestigationWorker
from app.workers.reporting_worker import ReportingWorker
from app.workers.response_worker import ResponseWorker
from app.schemas.contracts import WorkerType

WORKER_REGISTRY: Dict[WorkerType, Type[BaseWorker]] = {
    "detection": DetectionWorker,
    "correlation": CorrelationWorker,
    "investigation": InvestigationWorker,
    "reporting": ReportingWorker,
    "response": ResponseWorker,
}


def get_worker(worker_type: WorkerType) -> BaseWorker:
    """Factory function returning an instance of the requested worker type."""
    worker_cls = WORKER_REGISTRY.get(worker_type)
    if not worker_cls:
        raise ValueError(f"Unknown worker type: {worker_type}. Supported: {list(WORKER_REGISTRY.keys())}")
    return worker_cls()
