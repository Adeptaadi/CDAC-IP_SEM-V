from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dateutil import parser


class TemporalCorrelator:
    """Performs sliding time-window grouping and sequence analysis on security events (Phase 6)."""

    def __init__(self, default_window_seconds: int = 600):
        self.default_window_seconds = default_window_seconds

    @staticmethod
    def parse_event_time(event: Dict[str, Any]) -> datetime:
        """Extracts and parses timestamp from an event record."""
        ts_val = (
            event.get("timestamp")
            or event.get("created_at")
            or event.get("detected_at")
            or event.get("time")
        )
        if isinstance(ts_val, datetime):
            return ts_val
        if isinstance(ts_val, str):
            try:
                return parser.isoparse(ts_val)
            except Exception:
                try:
                    return datetime.fromisoformat(ts_val)
                except Exception:
                    pass
        return datetime.utcnow()

    def sort_chronologically(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sorts events in ascending chronological order."""
        return sorted(events, key=self.parse_event_time)

    def group_by_sliding_window(
        self,
        events: List[Dict[str, Any]],
        window_seconds: Optional[int] = None,
    ) -> List[List[Dict[str, Any]]]:
        """Partitions chronologically ordered events into temporal clusters based on a maximum inter-event gap or max window span."""
        if not events:
            return []

        sorted_events = self.sort_chronologically(events)
        max_gap = timedelta(seconds=window_seconds or self.default_window_seconds)

        clusters: List[List[Dict[str, Any]]] = []
        current_cluster: List[Dict[str, Any]] = [sorted_events[0]]
        cluster_start = self.parse_event_time(sorted_events[0])

        for ev in sorted_events[1:]:
            ev_time = self.parse_event_time(ev)
            prev_time = self.parse_event_time(current_cluster[-1])

            # If within gap of previous event and within 3x window from cluster start
            if (ev_time - prev_time) <= max_gap and (ev_time - cluster_start) <= (max_gap * 3):
                current_cluster.append(ev)
            else:
                clusters.append(current_cluster)
                current_cluster = [ev]
                cluster_start = ev_time

        if current_cluster:
            clusters.append(current_cluster)

        return clusters

    def calculate_temporal_similarity(self, time1: datetime, time2: datetime, max_delta_seconds: float = 3600.0) -> float:
        """Calculates temporal closeness score T in [0.0, 1.0] using exponential decay."""
        delta_sec = abs((time1 - time2).total_seconds())
        if delta_sec >= max_delta_seconds:
            return 0.0
        # Decay function: 1.0 at 0 distance, ~0.37 at delta=tau
        tau = max_delta_seconds / 3.0
        import math
        return round(float(math.exp(-delta_sec / max(1.0, tau))), 4)


temporal_correlator_instance = TemporalCorrelator()
