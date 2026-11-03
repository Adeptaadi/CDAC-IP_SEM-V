import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.dataset import Dataset, DatasetFile, ReplaySession, GroundTruthLabel
from app.repositories.base import BaseRepository


class DatasetRepository(BaseRepository[Dataset]):
    def __init__(self, db: Session):
        super().__init__(Dataset, db)

    def register_dataset(
        self,
        name: str,
        dataset_type: str,
        version: Optional[str] = "1.0.0",
        description: Optional[str] = None,
        source: Optional[str] = None,
        checksum: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dataset:
        ds = Dataset(
            name=name,
            version=version,
            description=description,
            source=source,
            dataset_type=dataset_type,
            checksum=checksum,
            dataset_metadata=metadata or {},
        )
        self.db.add(ds)
        self.db.flush()
        return ds

    def add_dataset_file(
        self,
        dataset_id: uuid.UUID,
        filename: str,
        storage_uri: str,
        file_format: str,
        file_size_bytes: Optional[int] = None,
        record_count: Optional[int] = None,
        checksum: Optional[str] = None,
        schema_metadata: Optional[Dict[str, Any]] = None,
    ) -> DatasetFile:
        df = DatasetFile(
            dataset_id=dataset_id,
            filename=filename,
            storage_uri=storage_uri,
            file_format=file_format,
            file_size_bytes=file_size_bytes,
            record_count=record_count,
            checksum=checksum,
            schema_metadata=schema_metadata or {},
            validation_status="valid",
        )
        self.db.add(df)
        self.db.flush()
        return df

    def create_replay_session(
        self,
        dataset_id: uuid.UUID,
        speed: float = 1.0,
        configuration: Optional[Dict[str, Any]] = None,
    ) -> ReplaySession:
        session = ReplaySession(
            dataset_id=dataset_id,
            status="pending",
            replay_speed=speed,
            configuration=configuration or {},
        )
        self.db.add(session)
        self.db.flush()
        return session

    def update_session_progress(
        self,
        session_id: uuid.UUID,
        records_read: int,
        records_accepted: int,
        records_rejected: int,
        status: Optional[str] = None,
    ) -> ReplaySession:
        session = self.db.query(ReplaySession).filter(ReplaySession.id == session_id).first()
        if not session:
            raise ValueError(f"ReplaySession {session_id} not found")

        session.records_read = records_read
        session.records_accepted = records_accepted
        session.records_rejected = records_rejected
        if status:
            session.status = status
            if status == "running" and not session.started_at:
                session.started_at = datetime.utcnow()
            elif status in ["completed", "failed", "cancelled"]:
                session.completed_at = datetime.utcnow()

        self.db.flush()
        return session

    def add_ground_truth_label(
        self,
        dataset_file_id: uuid.UUID,
        source_record_id: str,
        label: str,
        evaluation_split: str = "benchmark",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GroundTruthLabel:
        """Isolated evaluation label registration."""
        gt = GroundTruthLabel(
            dataset_file_id=dataset_file_id,
            source_record_id=source_record_id,
            label=label,
            evaluation_split=evaluation_split,
            label_metadata=metadata or {},
        )
        self.db.add(gt)
        self.db.flush()
        return gt
