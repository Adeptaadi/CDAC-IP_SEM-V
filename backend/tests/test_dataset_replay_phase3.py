import pytest
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
import app.models
from app.ingest.validator import DatasetValidator
from app.ingest.replayer import TelemetryReplayer, ReplayState
from app.ingest.ground_truth import GroundTruthService, GroundTruthAccessViolation
from app.models.dataset import Dataset, DatasetFile, ReplaySession, GroundTruthLabel

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


def test_dataset_validator_file_inspection():
    # 1. Validate infiltration normalized file
    import os
    from app.ingest.downloader import NORMALIZED_DIR, RAW_DIR
    from app.ingest.downloader import prepare_scenario
    from app.ingest.normalizer import TelemetryNormalizer

    prepare_scenario("infiltration")
    norm_path = TelemetryNormalizer.normalize_scenario_file("infiltration")

    meta = DatasetValidator.inspect_and_validate_file(norm_path)
    assert meta["file_format"] == "jsonl"
    assert meta["record_count"] >= 7
    assert meta["validation_status"] == "valid"
    assert len(meta["checksum"]) == 64  # SHA-256 hex string
    assert "timestamp" in meta["columns"]
    assert "event_type" in meta["columns"]


def test_dataset_validator_database_registration():
    db = TestSession()
    try:
        reg_result = DatasetValidator.register_scenario_dataset("brute_force", db)
        assert reg_result.get("dataset_id") is not None
        assert reg_result["raw_file"]["records"] >= 8
        assert reg_result["normalized_file"]["status"] == "valid"

        # Verify database entities
        ds = db.query(Dataset).first()
        assert ds is not None
        assert "Brute Force" in ds.name

        files = db.query(DatasetFile).filter(DatasetFile.dataset_id == ds.id).all()
        assert len(files) == 2  # raw and normalized
    finally:
        db.close()


def test_telemetry_replayer_step_and_lifecycle():
    replayer = TelemetryReplayer()
    replayer.load_scenario("infiltration", speed=5.0, batch_size=2)
    assert replayer.state == ReplayState.IDLE
    assert len(replayer.events) >= 7

    # Dispatched callback verification
    dispatched_events = []
    replayer.register_callback(lambda evt: dispatched_events.append(evt))

    # Step 2 events
    batch1 = replayer.step(count=2)
    assert len(batch1) == 2
    assert len(dispatched_events) == 2
    assert replayer.current_index == 2
    assert replayer.state == ReplayState.PAUSED

    # Step 3 events
    batch2 = replayer.step(count=3)
    assert len(batch2) == 3
    assert len(dispatched_events) == 5
    assert replayer.current_index == 5

    # Cancel replay
    replayer.cancel()
    assert replayer.state == ReplayState.CANCELLED

    # Reset replay
    replayer.reset()
    assert replayer.state == ReplayState.IDLE
    assert replayer.current_index == 0


def test_ground_truth_isolation_and_access_control():
    db = TestSession()
    try:
        # Register a dataset file
        ds = Dataset(name="Test Dataset", dataset_type="network_flow")
        db.add(ds)
        db.flush()

        df = DatasetFile(
            dataset_id=ds.id,
            filename="test_file.csv",
            storage_uri="/tmp/test.csv",
            file_format="csv",
            validation_status="valid",
        )
        db.add(df)
        db.commit()

        # Extract and register ground truth labels
        count = GroundTruthService.extract_and_register_labels(
            scenario_id="infiltration",
            dataset_file_id=df.id,
            db=db,
        )
        assert count >= 4  # 1 gold hypothesis + at least 3 MITRE techniques

        # 1. Authorized caller succeeds
        labels = GroundTruthService.get_evaluation_labels(
            dataset_file_id=df.id,
            db=db,
            caller_id="benchmark_runner",
        )
        assert len(labels) == count
        assert any("powershell" in l.label.lower() or "macro" in l.label.lower() for l in labels)

        # 2. Unauthorized caller (e.g. DetectionWorker or Planner) MUST be blocked
        with pytest.raises(GroundTruthAccessViolation):
            GroundTruthService.get_evaluation_labels(
                dataset_file_id=df.id,
                db=db,
                caller_id="detection_worker",
            )

        with pytest.raises(GroundTruthAccessViolation):
            GroundTruthService.get_evaluation_labels(
                dataset_file_id=df.id,
                db=db,
                caller_id="planner_engine",
            )
    finally:
        db.close()
