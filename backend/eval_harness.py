#!/usr/bin/env python3
"""Project Sentinel - Scientific Benchmark Evaluation Harness (P1).

Runs end-to-end autonomous threat hunting across all 5 CSE-CIC-IDS2018 scenarios
using the genuine EvaluationService to measure:
- Planner adaptivity, capability diversity, and replanning
- Worker execution success rates and evidence yields
- Evidence provenance completeness
- Accuracy, evidence coverage, hallucination rate, and ECE
"""

import sys
import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.eval.service import evaluation_service_instance


def run_standalone_evaluation():
    print("=" * 84)
    print("PROJECT SENTINEL: SYSTEM VALIDATION & PERFORMANCE OBSERVABILITY HARNESS (P1)")
    print("CSE-CIC-IDS2018 5-Scenario Autonomous Multi-Agent Hunting Validation")
    print("=" * 84)

    # Use in-memory SQLite for clean evaluation run
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=test_engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = Session()

    try:
        print("\n[+] Starting evaluation across all 5 registered CSE-CIC-IDS2018 scenarios...")
        start_time = datetime.now()
        scenario_results = evaluation_service_instance.evaluate_all(db, max_cycles=6)
        aggregate = evaluation_service_instance.get_aggregate_summary(db)
        elapsed = (datetime.now() - start_time).total_seconds()

        print("\n" + "=" * 84)
        print("PER-SCENARIO RESULTS:")
        print("=" * 84)
        for r in scenario_results:
            sc = r.scenario
            inv = r.investigation
            pl = r.planner
            ag = r.agents
            ev = r.evidence
            bm = r.benchmark_scores

            print(f"\n[{r.status.upper()}] Scenario: {sc.name} ({sc.scenario_id})")
            print(f"  • Source Profile:       {sc.source_type} ({sc.benchmark_basis})")
            print(f"  • Attack Category:      {sc.attack_type or 'N/A'}")
            print(f"  • Planning Cycles:      {inv.planning_cycles} cycles (Termination: {inv.termination_reason})")
            print(f"  • Confidence Delta:     {inv.initial_confidence} -> {inv.final_confidence} (Δ {inv.confidence_delta:+.4f})")
            print(f"  • Planner Diversity:    {pl.capability_diversity:.2f} ({pl.unique_capabilities} unique / {pl.total_selections} total)")
            print(f"  • Replanning Events:    {pl.replanning_events} | Capability Revisits: {pl.capability_revisits}")
            if pl.revisit_sequences:
                print(f"    - Revisit Sequences:  {', '.join(pl.revisit_sequences)}")
            print(f"  • Worker Success Rate:  {ag.execution_success_rate:.1f}% ({ag.successful_executions}/{ag.total_executions} executions)")
            print(f"  • Evidence Produced:    {ev.total_items} items (Direct: {ev.direct_provenance_items}, Derived: {ev.derived_provenance_items}, Legacy: {ev.legacy_unlinked_items})")
            print(f"  • Benchmark Scores:     Accuracy: {bm.accuracy*100:.1f}% | Coverage: {bm.evidence_coverage*100:.1f}% | Hallucination: {bm.hallucination_rate*100:.1f}% | ECE: {bm.expected_calibration_error:.4f}")

            # Per-worker breakdown
            print("  • Worker Execution Breakdown:")
            for w in ag.worker_metrics:
                print(f"    - {w.worker_type:<15} ({w.capability_name:<25}): {w.sample_size_repr:<22} Yield: {w.total_evidence_produced} ev, Latency: {w.average_latency_ms:.1f}ms")

        print("\n" + "=" * 84)
        print("AGGREGATE BENCHMARK OBSERVABILITY SUMMARY:")
        print("=" * 84)
        print(f"  • Total Scenarios Evaluated:         {aggregate.unique_scenarios_evaluated} ({', '.join(aggregate.scenarios_evaluated_list)})")
        print(f"  • Average Planning Cycles:          {aggregate.average_planning_cycles} cycles")
        print(f"  • Average Investigation Duration:    {aggregate.average_investigation_duration_ms:.1f} ms")
        print(f"  • Average Confidence Delta:         {aggregate.average_confidence_delta:+.4f}")
        print(f"  • Average Evidence Per Run:         {aggregate.average_evidence_per_investigation:.1f} items")
        print(f"  • Total Replanning Events:          {aggregate.total_replanning_events}")
        print(f"  • Total Capability Revisits:        {aggregate.total_capability_revisits}")
        print(f"  • Overall Worker Success Rate:      {aggregate.overall_agent_success_sample}")
        print(f"  • Most Selected Capability:         {aggregate.most_frequently_selected_capability}")
        print(f"  • Most Revisited Capability:        {aggregate.most_frequently_revisited_capability}")
        print(f"  • Highest Evidence Yield Worker:    {aggregate.highest_evidence_yield_capability}")
        print(f"  • Transparency Statement:           {aggregate.sample_size_population_statement}")
        print(f"  • Total Execution Elapsed Time:     {elapsed:.2f} s")
        print("=" * 84)

        # Output JSON report
        out_file = "evaluation_results_p1.json"
        export_payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "aggregate_metrics": aggregate.model_dump(),
            "scenario_results": [r.model_dump() for r in scenario_results],
        }
        with open(out_file, "w") as f:
            json.dump(export_payload, f, indent=2)
        print(f"\n[✓] Detailed P1 evaluation results exported to {out_file}")

        print("\n" + "=" * 84)
        print("SYSTEM VALIDATION & BENCHMARK OBSERVABILITY COMPLETE ✅")
        print("=" * 84)

        return export_payload

    finally:
        db.close()


if __name__ == "__main__":
    run_standalone_evaluation()
