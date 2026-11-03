import uuid
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from app.detection.contracts import DetectionFindingPayload


class FlowFeatureExtractor:
    """Zero-leakage flow feature extractor for network telemetry."""

    @staticmethod
    def extract_features(event: Dict[str, Any]) -> Dict[str, float]:
        """Extracts strictly non-leaked numerical flow features from event telemetry."""
        # Cleanly ignore any label/ground_truth fields to prevent target leakage
        data = event.get("normalized_data") or event.get("raw_log") or event

        port = float(event.get("destination_port") or event.get("dest_port") or data.get("dest_port") or data.get("Dst Port") or 80)
        bytes_sent = float(data.get("bytes_sent") or data.get("TotLen Fwd Pkts") or data.get("Flow Bytes/s") or data.get("Flow Bytes/Sec") or 100)
        packets_sent = float(data.get("packets_sent") or data.get("Tot Fwd Pkts") or data.get("Total Fwd Packets") or data.get("Flow Packets/s") or 5)
        duration = float(data.get("duration_ms") or data.get("Flow Duration") or 500)

        return {
            "dest_port": port,
            "bytes_sent": bytes_sent,
            "packets_sent": packets_sent,
            "duration_ms": duration,
        }


class MLDetectionEngine:
    """Statistical & Machine Learning Anomaly Detection Engine for Network Telemetry (Phase 5).

    Extracts flow features and detects anomalies with zero-leakage isolation.
    """

    MODEL_NAME = "BaselineFlowAnomalyDetector"
    MODEL_VERSION = "1.0.0"

    # Baseline statistical reference distributions for CSE-CIC-IDS2018 benign network traffic
    BENIGN_FEATURE_MEANS = {
        "dest_port": 443.0,
        "bytes_sent": 2500.0,
        "packets_sent": 15.0,
        "duration_ms": 1200.0,
    }
    BENIGN_FEATURE_STDS = {
        "dest_port": 1200.0,
        "bytes_sent": 8000.0,
        "packets_sent": 45.0,
        "duration_ms": 3500.0,
    }

    def __init__(self, feature_extractor: Optional[FlowFeatureExtractor] = None):
        self.extractor = feature_extractor or FlowFeatureExtractor()

    def extract_features(self, event: Dict[str, Any]) -> Dict[str, float]:
        """Extracts strictly non-leaked numerical flow features from event telemetry."""
        return self.extractor.extract_features(event)

    def compute_anomaly_score(self, features: Dict[str, float]) -> float:
        """Computes standardized statistical distance (Z-score norm) from benign profile."""
        z_scores = []
        for feat, val in features.items():
            mean = self.BENIGN_FEATURE_MEANS.get(feat, 1.0)
            std = max(1.0, self.BENIGN_FEATURE_STDS.get(feat, 1.0))
            z = abs(val - mean) / std
            z_scores.append(z)

        # Average normalized deviation mapped via sigmoid to [0.0, 1.0]
        avg_z = sum(z_scores) / max(1, len(z_scores))
        anomaly_score = 1.0 / (1.0 + math.exp(-0.8 * (avg_z - 3.0)))
        return round(float(anomaly_score), 4)

    def evaluate_event(self, event: Dict[str, Any], threshold: float = 0.65) -> Optional[DetectionFindingPayload]:
        """Evaluates event with ML anomaly scoring; produces finding if anomaly score exceeds threshold."""
        features = self.extract_features(event)
        score = self.compute_anomaly_score(features)

        if score < threshold:
            return None

        event_id = event.get("id") or event.get("event_id") or uuid.uuid4()
        if isinstance(event_id, str):
            try:
                event_id = uuid.UUID(event_id)
            except ValueError:
                event_id = uuid.uuid4()

        host = event.get("source_identifier") or event.get("host")
        user = event.get("user")
        src_ip = event.get("source_ip") or event.get("src_ip")
        dest_ip = event.get("destination_ip") or event.get("dest_ip")

        severity = "critical" if score >= 0.88 else ("high" if score >= 0.75 else "medium")

        return DetectionFindingPayload(
            finding_id=uuid.uuid4(),
            event_id=event_id,
            detection_method="ml",
            model_name=self.MODEL_NAME,
            model_version=self.MODEL_VERSION,
            predicted_class="Statistical Network Flow Anomaly",
            severity=severity,
            confidence=score,
            mitre_tactics=["Defense Evasion", "Command and Control", "Impact"],
            mitre_techniques=["T1071", "T1498"],
            explanation=(
                f"Statistical flow analysis detected abnormal network metrics "
                f"(anomaly score: {score:.2f}, dest_port: {int(features['dest_port'])}, "
                f"bytes: {int(features['bytes_sent'])})."
            ),
            details={
                "model": self.MODEL_NAME,
                "version": self.MODEL_VERSION,
                "anomaly_score": score,
                "features": features,
            },
            entity_refs={
                "hosts": [host] if host else [],
                "users": [user] if user else [],
                "ips": [ip for ip in [src_ip, dest_ip] if ip],
            },
            detected_at=datetime.utcnow(),
        )


ml_detection_engine_instance = MLDetectionEngine()
