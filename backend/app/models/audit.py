from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Integer, BigInteger
)
from app.database import Base
from app.models.base import GUID, JSONB_TYPE


class AuditLog(Base):
    __tablename__ = "audit_log"

    audit_id = Column(Integer().with_variant(BigInteger, "postgresql"), primary_key=True, autoincrement=True)
    investigation_id = Column(GUID, ForeignKey("investigations.investigation_id"), nullable=True)
    actor_type = Column(String(20), nullable=False)  # system, planner, worker, analyst
    actor_id = Column(String(100), nullable=True)
    action = Column(String(100), nullable=False)
    details = Column(JSONB_TYPE, nullable=True)
    occurred_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
