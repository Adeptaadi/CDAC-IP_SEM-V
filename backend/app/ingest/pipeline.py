import os
import json
import csv
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.schemas.contracts import CanonicalSecurityEvent, RejectedRecord
from app.ingest.normalizer import TelemetryNormalizer
from app.repositories.event_repo import SecurityEventRepository


class IngestionStats(BaseModel):
    source_file: str
    total_records: int = 0
    inserted_count: int = 0
    rejected_count: int = 0
    duration_seconds: float = 0.0
    throughput_eps: float = 0.0
    rejected_samples: List[RejectedRecord] = Field(default_factory=list)


class EventIngestionPipeline:
    """High-throughput Ingestion Pipeline converting raw datasets into canonical PostgreSQL SecurityEvents (Phase 4)."""

    def __init__(self, db: Session, batch_size: int = 500):
        self.db = db
        self.batch_size = max(10, batch_size)
        self.event_repo = SecurityEventRepository(db)

    def ingest_file(
        self,
        file_path: str,
        replay_session_id: Optional[uuid.UUID] = None,
        dataset_file_id: Optional[uuid.UUID] = None,
    ) -> IngestionStats:
        """Parses, normalizes, and batch-persists raw records from file into PostgreSQL."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        start_time = time.time()
        filename = os.path.basename(file_path)
        stats = IngestionStats(source_file=filename)

        valid_batch: List[Dict[str, Any]] = []

        def flush_batch():
            if valid_batch:
                self.event_repo.bulk_insert_events(valid_batch)
                self.db.commit()
                stats.inserted_count += len(valid_batch)
                valid_batch.clear()

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            first_char = f.read(1)
            f.seek(0)

            if first_char == "[":
                # JSON array format
                try:
                    records = json.load(f)
                    stats.total_records = len(records)
                    for idx, row in enumerate(records):
                        self._process_record(
                            raw=row,
                            row_idx=idx,
                            filename=filename,
                            replay_session_id=replay_session_id,
                            dataset_file_id=dataset_file_id,
                            valid_batch=valid_batch,
                            stats=stats,
                        )
                        if len(valid_batch) >= self.batch_size:
                            flush_batch()
                except Exception as e:
                    stats.rejected_count += 1
                    stats.rejected_samples.append(
                        RejectedRecord(
                            source_file=filename,
                            reason=f"Corrupt JSON payload: {str(e)}",
                        )
                    )

            elif file_path.endswith(".jsonl"):
                # JSONL format
                for idx, line in enumerate(f):
                    line_str = line.strip()
                    if not line_str:
                        continue
                    stats.total_records += 1
                    try:
                        row = json.loads(line_str)
                        self._process_record(
                            raw=row,
                            row_idx=idx,
                            filename=filename,
                            replay_session_id=replay_session_id,
                            dataset_file_id=dataset_file_id,
                            valid_batch=valid_batch,
                            stats=stats,
                        )
                        if len(valid_batch) >= self.batch_size:
                            flush_batch()
                    except Exception as e:
                        stats.rejected_count += 1
                        stats.rejected_samples.append(
                            RejectedRecord(
                                source_file=filename,
                                source_record_id=f"line-{idx}",
                                reason=f"Malformed JSONL line: {str(e)}",
                            )
                        )

            else:
                # CSV format
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader):
                    stats.total_records += 1
                    self._process_record(
                        raw=dict(row),
                        row_idx=idx,
                        filename=filename,
                        replay_session_id=replay_session_id,
                        dataset_file_id=dataset_file_id,
                        valid_batch=valid_batch,
                        stats=stats,
                    )
                    if len(valid_batch) >= self.batch_size:
                        flush_batch()

        # Flush any remaining items in final batch
        flush_batch()

        duration = max(0.001, time.time() - start_time)
        stats.duration_seconds = round(duration, 4)
        stats.throughput_eps = round(stats.inserted_count / duration, 2)
        return stats

    def _process_record(
        self,
        raw: Dict[str, Any],
        row_idx: int,
        filename: str,
        replay_session_id: Optional[uuid.UUID],
        dataset_file_id: Optional[uuid.UUID],
        valid_batch: List[Dict[str, Any]],
        stats: IngestionStats,
    ):
        source_record_id = f"{filename}#rec-{row_idx}"
        try:
            event, rejection = TelemetryNormalizer.to_canonical_security_event(
                raw=raw,
                replay_session_id=replay_session_id,
                dataset_file_id=dataset_file_id,
                source_record_id=source_record_id,
            )

            if rejection:
                stats.rejected_count += 1
                if len(stats.rejected_samples) < 10:
                    stats.rejected_samples.append(rejection)
                return

            if event:
                valid_batch.append({
                    "id": str(event.id),
                    "replay_session_id": str(event.replay_session_id) if event.replay_session_id else None,
                    "dataset_file_id": str(event.dataset_file_id) if event.dataset_file_id else None,
                    "source_record_id": event.source_record_id,
                    "event_type": event.event_type,
                    "event_timestamp": event.event_timestamp,
                    "ingestion_timestamp": event.ingestion_timestamp,
                    "source_ip": event.source_ip,
                    "destination_ip": event.destination_ip,
                    "source_port": event.source_port,
                    "destination_port": event.destination_port,
                    "protocol": event.protocol,
                    "source_identifier": event.source_identifier,
                    "normalized_data": event.normalized_data,
                    "normalization_version": event.normalization_version,
                    "content_hash": event.content_hash,
                })
        except Exception as e:
            stats.rejected_count += 1
            if len(stats.rejected_samples) < 10:
                stats.rejected_samples.append(
                    RejectedRecord(
                        source_file=filename,
                        source_record_id=source_record_id,
                        reason=f"Processing exception: {str(e)}",
                        raw_data=raw,
                    )
                )
