import os
import pytest
from datetime import datetime, timedelta
from app.ingest.scenarios import list_scenarios, get_scenario, SCENARIO_REGISTRY
from app.ingest.downloader import prepare_scenario, generate_synthetic_scenario_events
from app.ingest.normalizer import TelemetryNormalizer
from app.ingest.aligner import TimelineAligner
from app.ingest.replayer import TelemetryReplayer, ReplayState
from app.planner.confidence import ConfidenceEngine
from app.schemas.contracts import TelemetryEvent, WorkerResult, Finding


def test_scenario_registry_has_all_five():
    scenarios = list_scenarios()
    assert len(scenarios) == 5
    expected_ids = {"infiltration", "brute_force", "web_attacks", "botnet_c2", "dos_goldeneye"}
    assert set(SCENARIO_REGISTRY.keys()) == expected_ids


def test_all_scenarios_have_mitre_mappings():
    for scen_id, scen in SCENARIO_REGISTRY.items():
        assert len(scen.mitre_tactics) > 0, f"{scen_id} missing tactics"
        assert len(scen.mitre_techniques) > 0, f"{scen_id} missing techniques"
        assert scen.gold_hypothesis, f"{scen_id} missing gold hypothesis"


def test_synthetic_scenario_generation():
    for scen_id in SCENARIO_REGISTRY:
        events = generate_synthetic_scenario_events(scen_id)
        assert len(events) >= 2, f"Scenario {scen_id} generated too few events"
        for ev in events:
            assert "timestamp" in ev
            assert "source" in ev
            assert "event_type" in ev


def test_telemetry_normalization():
    raw_sample = {
        "timestamp": "2026-09-01T12:00:00Z",
        "source": "sysmon",
        "event_type": "process_creation",
        "host": "TEST-HOST-01",
        "user": "corp\\admin",
        "src_ip": "10.0.0.5",
        "dest_ip": None,
        "process_name": "cmd.exe",
        "command_line": "cmd.exe /c whoami",
        "raw_log": {"EventID": 1}
    }
    normalized = TelemetryNormalizer.normalize_event(raw_sample)
    assert isinstance(normalized, TelemetryEvent)
    assert normalized.host == "TEST-HOST-01"
    assert normalized.process_name == "cmd.exe"
    assert normalized.command_line == "cmd.exe /c whoami"


def test_timeline_aligner():
    base = datetime(2026, 1, 1, 0, 0, 0)
    e1 = TelemetryEvent(source="test", event_type="e1", timestamp=base)
    e2 = TelemetryEvent(source="test", event_type="e2", timestamp=base + timedelta(seconds=10))

    new_start = datetime(2026, 9, 1, 10, 0, 0)
    aligned = TimelineAligner.align_events([e1, e2], start_time=new_start)

    assert len(aligned) == 2
    assert aligned[0].timestamp == new_start
    assert aligned[1].timestamp == new_start + timedelta(seconds=10)


def test_telemetry_replayer_instant_mode():
    prepare_scenario("brute_force")
    TelemetryNormalizer.normalize_scenario_file("brute_force")

    replayer = TelemetryReplayer()
    replayer.load_scenario("brute_force", speed=float("inf"))
    assert replayer.state == ReplayState.IDLE
    assert len(replayer.events) > 0

    import asyncio

    async def _run():
        await replayer.start()
        if replayer._task:
            await replayer._task

    asyncio.run(_run())

    status = replayer.get_status()
    assert status["state"] == "COMPLETED"
    assert status["dispatched_events_count"] == len(replayer.events)
    assert status["progress_percent"] == 100.0


def test_confidence_engine_bounded_update():
    engine = ConfidenceEngine()
    result = WorkerResult(
        task_id="00000000-0000-0000-0000-000000000001",
        worker_type="detection",
        status="success",
        confidence_signal=0.85,
        findings=[Finding(description="Test suspicious finding", entity_refs={"hosts": ["H1"]})],
        reasoning_summary="Detection identified anomalous behavior."
    )
    factors = engine.compute_factors(
        worker_result=result,
        evidence_count_this_cycle=3,
        distinct_sources=2,
        total_evidence=3,
        corroborated=True,
    )
    delta = engine.compute_delta(factors)
    updated_conf = engine.update(current_confidence=0.30, delta=delta)

    # Must stay bounded strictly within (0, 1)
    assert 0.0 < updated_conf < 1.0
    assert updated_conf > 0.30  # confidence should rise
