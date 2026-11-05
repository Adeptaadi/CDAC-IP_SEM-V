"""Scientific Evaluation Metrics Engine for Project Sentinel (Phase 13).

Implements mathematical evaluation metrics defined in Implementation Specification:
1. Detection Metrics: Precision, Recall, F1, FPR, Balanced Accuracy, Macro F1, Weighted F1
2. Orchestration & Planning Metrics: Routing Precision, Replanning Effectiveness, Task Success Rate
3. Evidence & Reporting Metrics: Evidence Completeness, Citation Coverage, Hallucination Rate, Report Completeness
4. Operational Metrics: MTTD, MTTI, Expected Calibration Error (ECE)
"""

import math
from typing import List, Dict, Any, Tuple, Optional


# ==========================================
# 1. Detection Evaluation Metrics (IS §13.5)
# ==========================================

def compute_confusion_matrix(y_true: List[int], y_pred: List[int]) -> Dict[str, int]:
    """Computes basic binary confusion matrix counts (TP, FP, TN, FN)."""
    tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 1)
    fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 1)
    tn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 0)
    fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 0)
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}


def compute_detection_metrics(y_true: List[int], y_pred: List[int]) -> Dict[str, float]:
    """Computes comprehensive binary detection metrics: Precision, Recall, F1, FPR, Balanced Accuracy."""
    if not y_true or len(y_true) != len(y_pred):
        return {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "fpr": 0.0,
            "balanced_accuracy": 0.0,
        }

    cm = compute_confusion_matrix(y_true, y_pred)
    tp, fp, tn, fn = cm["tp"], cm["fp"], cm["tn"], cm["fn"]

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    balanced_acc = (recall + specificity) / 2.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "fpr": round(fpr, 4),
        "specificity": round(specificity, 4),
        "balanced_accuracy": round(balanced_acc, 4),
    }


def compute_multiclass_metrics(y_true: List[str], y_pred: List[str]) -> Dict[str, float]:
    """Computes Macro F1 and Weighted F1 across multiple attack class labels."""
    if not y_true or len(y_true) != len(y_pred):
        return {"macro_f1": 0.0, "weighted_f1": 0.0}

    classes = sorted(list(set(y_true).union(set(y_pred))))
    f1_scores = {}
    supports = {}

    for cls in classes:
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == cls and yp == cls)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt != cls and yp == cls)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == cls and yp != cls)
        support = sum(1 for yt in y_true if yt == cls)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        f1_scores[cls] = f1
        supports[cls] = support

    macro_f1 = sum(f1_scores.values()) / len(classes) if classes else 0.0
    total_support = sum(supports.values())
    weighted_f1 = (
        sum(f1_scores[c] * supports[c] for c in classes) / total_support
        if total_support > 0
        else 0.0
    )

    return {
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
    }


# ==========================================
# 2. Evidence and Reporting Metrics (IS §13.7)
# ==========================================

def compute_evidence_coverage(extracted_techniques: List[str], gold_techniques: List[str]) -> float:
    """Computes Evidence Coverage: |E_found ∩ E_gold| / |E_gold|."""
    if not gold_techniques:
        return 1.0
    extracted_set = set(t.strip().upper() for t in extracted_techniques if t)
    gold_set = set(t.strip().upper() for t in gold_techniques if t)

    intersection = extracted_set.intersection(gold_set)
    coverage = len(intersection) / len(gold_set)
    return round(coverage, 4)


def compute_evidence_precision(extracted_evidence_refs: List[str], gold_relevant_refs: List[str]) -> float:
    """Computes Evidence Precision: |E_found ∩ E_gold| / |E_found|."""
    if not extracted_evidence_refs:
        return 1.0
    found_set = set(str(r).strip() for r in extracted_evidence_refs if r)
    gold_set = set(str(r).strip() for r in gold_relevant_refs if r)
    if not found_set:
        return 1.0
    return round(len(found_set.intersection(gold_set)) / len(found_set), 4)


def compute_citation_coverage(claims: List[Dict[str, Any]], verified_evidence_ids: List[str]) -> float:
    """Computes Citation Coverage: Proportion of claims that cite valid verified evidence."""
    if not claims:
        return 1.0
    verified_set = set(str(eid) for eid in verified_evidence_ids)
    cited_claims = 0
    for claim in claims:
        citations = claim.get("evidence_ids", []) or claim.get("evidence_refs", [])
        if citations and any(str(c) in verified_set for c in citations):
            cited_claims += 1
    return round(cited_claims / len(claims), 4)


def compute_hallucination_rate(claims: List[Dict[str, Any]], verified_evidence_ids: List[str]) -> float:
    """Computes Hallucination Rate: proportion of claims lacking grounded evidence citations (1.0 - Citation Coverage)."""
    return round(1.0 - compute_citation_coverage(claims, verified_evidence_ids), 4)


def compute_report_completeness(report_dict: Dict[str, Any], required_sections: Optional[List[str]] = None) -> float:
    """Computes the completeness of a 7-section forensic report."""
    default_sections = [
        "executive_summary",
        "attack_narrative",
        "scope_of_compromise",
        "timeline",
        "mitre_matrix",
        "containment_actions",
        "confidence_assessment",
    ]
    sections = required_sections or default_sections
    if not sections:
        return 1.0

    present_count = 0
    for sec in sections:
        val = report_dict.get(sec)
        if val is not None:
            if isinstance(val, (str, list, dict)) and len(val) > 0:
                present_count += 1
            elif isinstance(val, (int, float)):
                present_count += 1

    return round(present_count / len(sections), 4)


# ==========================================
# 3. Orchestration & Operational Metrics (IS §13.6, §1.3)
# ==========================================

def compute_planner_routing_precision(decisions: List[Dict[str, Any]]) -> float:
    """Computes Planner Routing Precision: proportion of planner-selected workers that produced valid findings."""
    if not decisions:
        return 0.0
    effective_actions = 0
    for d in decisions:
        action = d.get("action") or d.get("decision_type")
        worker_res = d.get("worker_result") or {}
        # If worker produced findings or delta in confidence or progressed state
        has_findings = bool(worker_res.get("findings") or worker_res.get("evidence_count"))
        has_progress = abs(float(d.get("confidence_delta", 0.0))) > 0.001
        if has_findings or has_progress or action in ["complete_investigation", "request_human_review"]:
            effective_actions += 1
    return round(effective_actions / len(decisions), 4)


def compute_replanning_effectiveness(replan_decisions: List[Dict[str, Any]]) -> float:
    """Computes Replanning Effectiveness: rate at which replan cycles improved confidence or gathered new leads."""
    if not replan_decisions:
        return 1.0  # No replanning failures
    successful_replans = sum(
        1 for d in replan_decisions
        if float(d.get("confidence_after", 0.0)) > float(d.get("confidence_before", 0.0))
        or bool(d.get("new_hypotheses_count", 0)) > 0
    )
    return round(successful_replans / len(replan_decisions), 4)


def compute_operational_latencies(
    detection_times_sec: List[float],
    investigation_times_sec: List[float]
) -> Dict[str, float]:
    """Computes Mean Time to Detect (MTTD) and Mean Time to Investigate (MTTI)."""
    mttd = sum(detection_times_sec) / len(detection_times_sec) if detection_times_sec else 0.0
    mtti = sum(investigation_times_sec) / len(investigation_times_sec) if investigation_times_sec else 0.0
    return {
        "mttd_seconds": round(mttd, 2),
        "mtti_seconds": round(mtti, 2),
    }


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

