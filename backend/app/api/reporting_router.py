import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.reporting import Report
from app.reporting import (
    reporting_service_instance,
    IncidentReportPayload,
    ReportValidationResult,
)

reporting_router = APIRouter(prefix="/api/reports", tags=["Investigation Reporting"])


@reporting_router.post("/generate/{investigation_id}", response_model=IncidentReportPayload, status_code=status.HTTP_201_CREATED)
def generate_report(
    investigation_id: uuid.UUID,
    title: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Compiles and persists a full incident report for an investigation (Phase 11)."""
    try:
        return reporting_service_instance.generate_report(investigation_id=investigation_id, db=db, title=title)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@reporting_router.get("/{report_id}", response_model=IncidentReportPayload)
def get_report(report_id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieves an existing incident report by ID."""
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return reporting_service_instance.generate_report(investigation_id=report.investigation_id, db=db)


@reporting_router.get("/investigation/{investigation_id}", response_model=IncidentReportPayload)
def get_report_by_investigation(investigation_id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieves or generates an incident report for an investigation."""
    try:
        return reporting_service_instance.generate_report(investigation_id=investigation_id, db=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@reporting_router.post("/validate", response_model=ReportValidationResult)
def validate_report(payload: IncidentReportPayload):
    """Audits an incident report against completeness, evidence, and provenance rules."""
    return reporting_service_instance.validate_report(payload)
