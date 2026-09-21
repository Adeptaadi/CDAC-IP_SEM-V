from abc import ABC, abstractmethod
from app.schemas.contracts import WorkerTask, WorkerResult, WorkerType


class BaseWorker(ABC):
    worker_type: WorkerType

    @abstractmethod
    def execute(self, task: WorkerTask) -> WorkerResult:
        """Executes the assigned investigation task and returns structured findings."""
        pass

    def health_check(self) -> bool:
        """Returns True if the worker is operational and dependencies are accessible."""
        return True
