from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.db import get_db
from app.models.db_models import ScanReportDB, ProjectDB

router = APIRouter(prefix="/reports", tags=["reports"])


class SeveritySummary(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class ToolSummary(BaseModel):
    tool: str
    findings: int
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    link: Optional[str] = None


class ReportSummary(BaseModel):
    project_id: str
    total_findings: int
    severity: SeveritySummary
    tools: List[ToolSummary]


class FindingItem(BaseModel):
    id: str
    severity: str
    title: str
    description: Optional[str] = None
    cve: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    service: Optional[str] = None
    uri: Optional[str] = None
    package: Optional[str] = None
    recommendation: Optional[str] = None


class ReportDetail(BaseModel):
    id: int
    scan_id: str
    tool: str
    severity_summary: SeveritySummary
    findings: List[FindingItem]
    report_url: Optional[str] = None
    created_at: str


@router.get("/projects/{project_id}/reports", response_model=List[ReportDetail])
def get_project_reports(project_id: str, db: Session = Depends(get_db)):
    """Get all reports for a project"""
    project = db.query(ProjectDB).filter(ProjectDB.project_id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    reports = db.query(ScanReportDB).filter(
        ScanReportDB.project_id == project_id
    ).order_by(ScanReportDB.created_at.desc()).all()

    return [
        ReportDetail(
            id=r.id,
            scan_id=r.scan_id,
            tool=r.tool_name,
            severity_summary=r.severity_summary or SeveritySummary(),
            findings=[FindingItem(**f) for f in (r.findings or [])],
            report_url=r.report_url,
            created_at=r.created_at.isoformat() if r.created_at else "",
        )
        for r in reports
    ]


@router.get("/projects/{project_id}/reports/summary", response_model=ReportSummary)
def get_reports_summary(project_id: str, db: Session = Depends(get_db)):
    """Get combined severity counts across all tools"""
    project = db.query(ProjectDB).filter(ProjectDB.project_id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    reports = db.query(ScanReportDB).filter(
        ScanReportDB.project_id == project_id
    ).all()

    total_findings = 0
    severity = SeveritySummary()
    tools = []

    for r in reports:
        summary = r.severity_summary or {}
        findings_count = sum(summary.values())
        total_findings += findings_count

        severity.critical += summary.get("critical", 0)
        severity.high += summary.get("high", 0)
        severity.medium += summary.get("medium", 0)
        severity.low += summary.get("low", 0)

        tool_link = r.report_url if r.tool_name == "sonar" else None

        tools.append(ToolSummary(
            tool=r.tool_name,
            findings=findings_count,
            critical=summary.get("critical", 0),
            high=summary.get("high", 0),
            medium=summary.get("medium", 0),
            low=summary.get("low", 0),
            link=tool_link,
        ))

    return ReportSummary(
        project_id=project_id,
        total_findings=total_findings,
        severity=severity,
        tools=tools,
    )


@router.get("/{report_id}", response_model=ReportDetail)
def get_report(report_id: int, db: Session = Depends(get_db)):
    """Get detailed report for a specific tool"""
    report = db.query(ScanReportDB).filter(ScanReportDB.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return ReportDetail(
        id=report.id,
        scan_id=report.scan_id,
        tool=report.tool_name,
        severity_summary=report.severity_summary or SeveritySummary(),
        findings=[FindingItem(**f) for f in (report.findings or [])],
        report_url=report.report_url,
        created_at=report.created_at.isoformat() if report.created_at else "",
    )


@router.get("/{report_id}/download")
def download_raw_report(report_id: int, db: Session = Depends(get_db)):
    """Download raw JSON report"""
    report = db.query(ScanReportDB).filter(ScanReportDB.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if not report.raw_report:
        raise HTTPException(status_code=404, detail="Raw report not available")

    return {
        "content": report.raw_report,
        "filename": f"{report.tool_name}_report.json",
        "content_type": "application/json",
    }


@router.delete("/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    """Delete a specific report"""
    report = db.query(ScanReportDB).filter(ScanReportDB.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    db.delete(report)
    db.commit()

    return {"status": "success", "message": f"Report {report_id} deleted"}
