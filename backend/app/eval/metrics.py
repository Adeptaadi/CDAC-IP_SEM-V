"""Scientific Evaluation Metrics Engine for Project Sentinel (Stage 5).

Implements mathematical metrics defined in SDD & Implementation Specification:
1. Planner Accuracy: Gold hypothesis matching rate
2. Evidence Coverage: |E_found ∩ E_gold| / |E_gold|
3. Hallucination Rate: |Unsubstantiated Claims| / |Total Claims|
4. Expected Calibration Error (ECE): ECE = ∑ (|B_m|/N) * |acc(B_m) - conf(B_m)|
"""

import math
from typing import List, Dict, Any, Tuple


def compute_evidence_coverage(extracted_techniques: List[str], gold_techniques: List[str]) -> float:
    """Computes Evidence Coverage: |E_found ∩ E_gold| / |E_gold|."""
    if not gold_techniques:
        return 1.0
    extracted_set = set(t.strip().upper() for t in extracted_techniques if t)
    gold_set = set(t.strip().upper() for t in gold_techniques if t)
    
    intersection = extracted_set.intersection(gold_set)
    coverage = len(intersection) / len(gold_set)
    return round(coverage, 4)


def compute_hallucination_rate(claims: List[Dict[str, Any]], verified_evidence_ids: List[str]) -> float:
    """Computes Hallucination Rate: proportion of worker claims lacking grounded evidence citations."""
    if not claims:
        return 0.0
    
    unsubstantiated = 0
    verified_set = set(str(eid) for eid in verified_evidence_ids)

    for claim in claims:
        # Check if claim has non-empty evidence citations that match known verified evidence
        citations = claim.get("evidence_ids", []) or claim.get("evidence_refs", [])
        if not citations:
            unsubstantiated += 1
        else:
            # Check if any citation matches verified evidence
            valid = any(str(c) in verified_set for c in citations)
            if not valid:
                unsubstantiated += 1

    return round(unsubstantiated / len(claims), 4)


def compute_expected_calibration_error(
    confidences: List[float],
    ground_truth_labels: List[int],
    num_bins: int = 5
) -> float:
    """Computes Expected Calibration Error (ECE) across M confidence bins.
    
    ECE = ∑_{m=1}^M (|B_m| / N) * |acc(B_m) - conf(B_m)|
    """
    n = len(confidences)
    if n == 0 or len(ground_truth_labels) != n:
        return 0.0

    bins = [[] for _ in range(num_bins)]
    bin_width = 1.0 / num_bins

    for conf, label in zip(confidences, ground_truth_labels):
        # Bound confidence in [0.0, 1.0]
        c = max(0.0, min(1.0, float(conf)))
        bin_idx = min(int(c / bin_width), num_bins - 1)
        bins[bin_idx].append((c, label))

    ece = 0.0
    for bin_items in bins:
        if not bin_items:
            continue
        bin_size = len(bin_items)
        avg_conf = sum(c for c, _ in bin_items) / bin_size
        avg_acc = sum(label for _, label in bin_items) / bin_size
        ece += (bin_size / n) * abs(avg_acc - avg_conf)

    return round(ece, 4)
