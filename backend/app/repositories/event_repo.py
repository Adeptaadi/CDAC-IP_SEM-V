import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.telemetry import SecurityEvent
from app.repositories.base import BaseRepository


class SecurityEventRepository(BaseRepository[SecurityEvent]):
    def __init__(self, db: Session):
        super().__init__(SecurityEvent, db)

    def create_event(
        self,
        event_type: str,
        event_timestamp: datetime,
        normalized_data: Dict[str, Any],
        replay_session_id: Optional[uuid.UUID] = None,
        dataset_file_id: Optional[uuid.UUID] = None,
        source_record_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        destination_ip: Optional[str] = None,
        source_port: Optional[int] = None,
        destination_port: Optional[int] = None,
        protocol: Optional[str] = None,
        source_identifier: Optional[str] = None,
        normalization_version: str = "1.0.0",
        content_hash: Optional[str] = None,
    ) -> SecurityEvent:
        event = SecurityEvent(
            event_type=event_type,
            event_timestamp=event_timestamp,
            ingestion_timestamp=datetime.utcnow(),
            normalized_data=normalized_data,
            replay_session_id=replay_session_id,
            dataset_file_id=dataset_file_id,
            source_record_id=source_record_id,
            source_ip=source_ip,
            destination_ip=destination_ip,
            source_port=source_port,
            destination_port=destination_port,
            protocol=protocol,
            source_identifier=source_identifier,
            normalization_version=normalization_version,
            content_hash=content_hash,
        )
        self.db.add(event)
        self.db.flush()
        return event

    def bulk_insert_events(self, events: List[Dict[str, Any]]) -> int:
        """High-throughput batch insertion for telemetry replay workloads."""
        if not events:
            return 0
        objects = [SecurityEvent(**evt) for evt in events]
        self.db.bulk_save_objects(objects)
        self.db.flush()
        return len(objects)

    def query_events_by_timerange(
        self,
        start_time: datetime,
        end_time: datetime,
        source_ip: Optional[str] = None,
        destination_ip: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 1000,
    ) -> List[SecurityEvent]:
        query = self.db.query(SecurityEvent).filter(
            and_(
                SecurityEvent.event_timestamp >= start_time,
                SecurityEvent.event_timestamp <= end_time,
            )
        )
        if source_ip:
            query = query.filter(SecurityEvent.source_ip == source_ip)
        if destination_ip:
            query = query.filter(SecurityEvent.destination_ip == destination_ip)
        if event_type:
            query = query.filter(SecurityEvent.event_type == event_type)

        return query.order_by(SecurityEvent.event_timestamp.asc()).limit(limit).all()
