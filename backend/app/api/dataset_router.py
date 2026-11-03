import uuid
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.database import get_db
from app.ingest.scenarios import list_scenarios, get_scenario, ScenarioMetadata
from app.ingest.downloader import prepare_scenario
from app.ingest.normalizer import TelemetryNormalizer
from app.ingest.replayer import replayer_instance
from app.ingest.validator import DatasetValidator
from app.models.dataset import ReplaySession

dataset_router = APIRouter(prefix="/api/dataset", tags=["Dataset & Telemetry Replay"])


@dataset_router.get("/scenarios", response_model=List[ScenarioMetadata])
def get_all_scenarios():
    """Returns the list of all 5 configured CSE-CIC-IDS2018 scenarios with MITRE mappings."""
    return list_scenarios()


@dataset_router.get("/scenarios/{scenario_id}", response_model=ScenarioMetadata)
def get_scenario_details(scenario_id: str):
    scen = get_scenario(scenario_id)
    if not scen:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scen


@dataset_router.post("/prepare/{scenario_id}")
def prepare_scenario_data(scenario_id: str):
    """Prepares and normalizes the scenario files on disk."""
    if not get_scenario(scenario_id):
        raise HTTPException(status_code=404, detail="Scenario not found")

    raw_path = prepare_scenario(scenario_id)
    norm_path = TelemetryNormalizer.normalize_scenario_file(scenario_id)
    return {
        "scenario_id": scenario_id,
        "status": "prepared",
        "raw_path": raw_path,
        "normalized_path": norm_path,
    }


@dataset_router.post("/validate/{scenario_id}")
def validate_scenario(scenario_id: str):
    """Inspects and validates dataset file headers, encoding, checksum, and record counts."""
    scen = get_scenario(scenario_id)
    if not scen:
        raise HTTPException(status_code=404, detail="Scenario not found")

    prepare_scenario(scenario_id)
    TelemetryNormalizer.normalize_scenario_file(scenario_id)

    raw_val = DatasetValidator.inspect_and_validate_file(scen.raw_filename) if False else None
    import os
    from app.ingest.downloader import RAW_DIR, NORMALIZED_DIR
    raw_path = os.path.join(RAW_DIR, scen.raw_filename)
    norm_path = os.path.join(NORMALIZED_DIR, scen.normalized_filename)

    raw_info = DatasetValidator.inspect_and_validate_file(raw_path)
    norm_info = DatasetValidator.inspect_and_validate_file(norm_path)

    return {
        "scenario_id": scenario_id,
        "raw_file": raw_info,
        "normalized_file": norm_info,
        "status": "valid" if norm_info["validation_status"] == "valid" else "warning",
    }


@dataset_router.post("/register/{scenario_id}")
def register_scenario_in_db(scenario_id: str, db: Session = Depends(get_db)):
    """Registers scenario metadata, raw file, and normalized file into PostgreSQL."""
    try:
        result = DatasetValidator.register_scenario_dataset(scenario_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@dataset_router.post("/replay/load/{scenario_id}")
def load_scenario_for_replay(scenario_id: str, speed: float = 1.0, batch_size: int = 50):
    """Loads a scenario into the live replayer."""
    try:
        replayer_instance.load_scenario(scenario_id, speed=speed, batch_size=batch_size)
        return replayer_instance.get_status()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@dataset_router.post("/replay/start")
async def start_replay():
    """Starts or resumes streaming replay of the loaded scenario."""
    try:
        await replayer_instance.start()
        return replayer_instance.get_status()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@dataset_router.post("/replay/step")
def step_replay(count: int = 1):
    """Dispatches next N events incrementally for interactive step debugging."""
    try:
        dispatched = replayer_instance.step(count=count)
        status_info = replayer_instance.get_status()
        status_info["dispatched_in_step"] = len(dispatched)
        return status_info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@dataset_router.post("/replay/pause")
def pause_replay():
    """Pauses streaming replay."""
    replayer_instance.pause()
    return replayer_instance.get_status()


@dataset_router.post("/replay/cancel")
def cancel_replay():
    """Cancels streaming replay."""
    replayer_instance.cancel()
    return replayer_instance.get_status()


@dataset_router.post("/replay/reset")
def reset_replay():
    """Resets the replayer back to T0."""
    replayer_instance.reset()
    return replayer_instance.get_status()


@dataset_router.get("/replay/status")
def get_replay_status():
    """Returns the current replay streaming state and metrics."""
    return replayer_instance.get_status()


@dataset_router.post("/ingest/{scenario_id}")
def ingest_scenario_into_db(scenario_id: str, db: Session = Depends(get_db)):
    """Executes the Phase 4 batch ingestion pipeline, parsing and storing canonical SecurityEvents."""
    scen = get_scenario(scenario_id)
    if not scen:
        raise HTTPException(status_code=404, detail="Scenario not found")

    from app.ingest.pipeline import EventIngestionPipeline
    from app.ingest.downloader import NORMALIZED_DIR
    import os

    TelemetryNormalizer.normalize_scenario_file(scenario_id)
    norm_path = os.path.join(NORMALIZED_DIR, scen.normalized_filename)

    pipeline = EventIngestionPipeline(db, batch_size=200)
    stats = pipeline.ingest_file(norm_path)
    return stats.model_dump()


@dataset_router.get("/replays")
def list_replay_sessions(db: Session = Depends(get_db)):
    """Lists persistent replay sessions from the database."""
    return db.query(ReplaySession).order_by(ReplaySession.created_at.desc()).limit(20).all()
