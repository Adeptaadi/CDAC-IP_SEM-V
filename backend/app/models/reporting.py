import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Numeric, DateTime, ForeignKey, Integer
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import GUID, JSONB_TYPE


class Report(Base):
    __tablename__ = "reports"

    report_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    investigation_id = Column(GUID, ForeignKey("investigations.investigation_id", ondelete="CASCADE"), nullable=False)
    executive_summary = Column(Text, nullable=False)
    technical_body = Column(Text, nullable=False)
    final_confidence = Column(Numeric(5, 4), nullable=False)
    generated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    approved_by_user_id = Column(GUID, ForeignKey("users.user_id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    investigation = relationship("Investigation", back_populates="reports")
    recommendations = relationship("Recommendation", back_populates="report", cascade="all, delete-orphan")
    sections = relationship("ReportSection", back_populates="report", cascade="all, delete-orphan")


class ReportSection(Base):
    __tablename__ = "report_sections"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    report_id = Column(GUID, ForeignKey("reports.report_id", ondelete="CASCADE"), nullable=False)
    section_title = Column(String(150), nullable=False)
    section_order = Column(Integer, default=0, nullable=False)
    content = Column(Text, nullable=False)
    section_metadata = Column("metadata", JSONB_TYPE, default=dict)

    report = relationship("Report", back_populates="sections")
