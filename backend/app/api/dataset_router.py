from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from app.ingest.scenarios import list_scenarios, get_scenario, ScenarioMetadata
from app.ingest.downloader import prepare_scenario
from app.ingest.normalizer import TelemetryNormalizer
from app.ingest.replayer import replayer_instance

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
        "normalized_path": norm_path
    }


@dataset_router.post("/replay/load/{scenario_id}")
def load_scenario_for_replay(scenario_id: str, speed: float = 1.0):
    """Loads a scenario into the live replayer."""
    try:
        replayer_instance.load_scenario(scenario_id, speed=speed)
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


@dataset_router.post("/replay/pause")
def pause_replay():
    """Pauses streaming replay."""
    replayer_instance.pause()
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
