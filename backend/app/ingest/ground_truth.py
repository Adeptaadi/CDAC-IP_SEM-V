import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.dataset import GroundTruthLabel
from app.ingest.scenarios import SCENARIO_REGISTRY
from app.repositories.dataset_repo import DatasetRepository


class GroundTruthAccessViolation(PermissionError):
    """Raised when an unauthorized service or agent attempts to access ground-truth labels."""
    pass


class GroundTruthService:
    """Evaluation-only service for ground-truth labels with strict target leakage isolation (Phase 3)."""

    AUTHORIZED_EVAL_CALLERS = {"benchmark_runner", "eval_harness", "evaluation_service"}

    @classmethod
    def assert_authorized_caller(cls, caller_id: str):
        if caller_id not in cls.AUTHORIZED_EVAL_CALLERS:
            raise GroundTruthAccessViolation(
                f"Unauthorized access to ground-truth labels by '{caller_id}'. "
                "Ground-truth labels are strictly isolated to evaluation harnesses to prevent target leakage."
            )

    @classmethod
    def extract_and_register_labels(
        cls,
        scenario_id: str,
        dataset_file_id: uuid.UUID,
        db: Session,
        split: str = "benchmark",
    ) -> int:
        """Registers gold scenario hypothesis and MITRE technique ground-truth labels."""
        scenario = SCENARIO_REGISTRY.get(scenario_id)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_id}")

        repo = DatasetRepository(db)
        registered_count = 0

        # 1. Register gold hypothesis label
        repo.add_ground_truth_label(
            dataset_file_id=dataset_file_id,
            source_record_id=f"{scenario_id}-gold-hypothesis",
            label=scenario.gold_hypothesis,
            evaluation_split=split,
            metadata={"type": "hypothesis", "tactics": scenario.mitre_tactics},
        )
        registered_count += 1

        # 2. Register MITRE technique labels
        for idx, tech in enumerate(scenario.mitre_techniques):
            repo.add_ground_truth_label(
                dataset_file_id=dataset_file_id,
                source_record_id=f"{scenario_id}-tech-{idx+1}",
                label=tech,
                evaluation_split=split,
                metadata={"type": "mitre_technique", "day": scenario.day},
            )
            registered_count += 1

        db.commit()
        return registered_count

    @classmethod
    def get_evaluation_labels(
        cls,
        dataset_file_id: uuid.UUID,
        db: Session,
        caller_id: str,
        split: Optional[str] = None,
    ) -> List[GroundTruthLabel]:
        """Retrieves ground-truth labels strictly for authorized evaluation callers."""
        cls.assert_authorized_caller(caller_id)

        query = db.query(GroundTruthLabel).filter(
            GroundTruthLabel.dataset_file_id == dataset_file_id
        )
        if split:
            query = query.filter(GroundTruthLabel.evaluation_split == split)

        return query.all()
