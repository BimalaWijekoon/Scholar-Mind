"""
Report Generation API Routes
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from enum import Enum

from backend.api.dependencies import get_query_service
from backend.services.report_service import ReportService


router = APIRouter()


class ReportType(str, Enum):
    """Report type enum."""
    LITERATURE_REVIEW = "literature_review"
    RESEARCH_GAP = "research_gap"
    TREND_ANALYSIS = "trend_analysis"
    COMPARISON = "comparison"
    SUMMARY = "summary"


class ExportFormat(str, Enum):
    """Export format enum."""
    PDF = "pdf"
    MARKDOWN = "markdown"
    WORD = "docx"
    HTML = "html"


class ReportRequest(BaseModel):
    """Report generation request model."""
    report_type: ReportType
    document_ids: List[str]
    title: Optional[str] = None
    topic: Optional[str] = None
    sections: Optional[List[str]] = None
    max_length: Optional[int] = None


class ReportResponse(BaseModel):
    """Report response model."""
    id: str
    title: str
    report_type: str
    status: str
    content: Optional[str] = None
    sections: Optional[List[dict]] = None
    created_at: str


def get_report_service() -> ReportService:
    """Get report service instance."""
    return ReportService()


@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks,
    report_service: ReportService = Depends(get_report_service),
):
    """
    Generate a research report based on selected documents.
    
    Report types:
    - literature_review: Comprehensive review of the literature
    - research_gap: Identify gaps and opportunities
    - trend_analysis: Analyze trends over time
    - comparison: Compare different approaches/methods
    - summary: Executive summary of documents
    """
    if len(request.document_ids) == 0:
        raise HTTPException(
            status_code=400,
            detail="At least one document ID is required",
        )
    
    result = await report_service.generate_report(
        report_type=request.report_type,
        document_ids=request.document_ids,
        title=request.title,
        topic=request.topic,
        sections=request.sections,
        max_length=request.max_length,
    )
    return result


@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    report_type: Optional[ReportType] = None,
    report_service: ReportService = Depends(get_report_service),
):
    """List all generated reports."""
    result = await report_service.list_reports(report_type=report_type)
    return result


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    report_service: ReportService = Depends(get_report_service),
):
    """Get a specific report by ID."""
    result = await report_service.get_report(report_id)
    if not result:
        raise HTTPException(status_code=404, detail="Report not found")
    return result


@router.post("/{report_id}/export")
async def export_report(
    report_id: str,
    format: ExportFormat,
    report_service: ReportService = Depends(get_report_service),
):
    """Export a report to the specified format."""
    result = await report_service.export_report(report_id, format)
    if not result:
        raise HTTPException(status_code=404, detail="Report not found")
    return result


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    report_service: ReportService = Depends(get_report_service),
):
    """Delete a report."""
    success = await report_service.delete_report(report_id)
    if not success:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"message": "Report deleted successfully"}


@router.post("/literature-review")
async def generate_literature_review(
    document_ids: List[str],
    topic: str,
    include_citations: bool = True,
    report_service: ReportService = Depends(get_report_service),
):
    """Generate a literature review for the given topic."""
    result = await report_service.generate_literature_review(
        document_ids=document_ids,
        topic=topic,
        include_citations=include_citations,
    )
    return result


@router.post("/research-gaps")
async def identify_research_gaps(
    document_ids: List[str],
    report_service: ReportService = Depends(get_report_service),
):
    """Identify research gaps based on the document corpus."""
    result = await report_service.identify_research_gaps(document_ids=document_ids)
    return result
