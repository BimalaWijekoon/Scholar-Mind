"""
Document Upload and Management API Routes
"""

from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from pydantic import BaseModel

from backend.api.dependencies import get_document_service
from backend.services.document_service import DocumentService


router = APIRouter()


class DocumentResponse(BaseModel):
    """Document response model."""
    id: str
    title: str
    filename: str
    file_type: str
    upload_date: str
    status: str
    page_count: Optional[int] = None
    authors: Optional[List[str]] = None
    abstract: Optional[str] = None


class DocumentListResponse(BaseModel):
    """Document list response model."""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Upload a document (PDF, Word, Text file).
    
    The document will be processed asynchronously:
    1. Parse and extract text
    2. Extract metadata (title, authors, abstract)
    3. Chunk the document
    4. Extract entities and relations
    5. Add to knowledge graph
    """
    allowed_types = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "text/markdown",
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: PDF, Word, Text, Markdown",
        )
    
    result = await document_service.upload_document(file)
    return result


@router.post("/upload-url", response_model=DocumentResponse)
async def upload_from_url(
    url: str,
    document_service: DocumentService = Depends(get_document_service),
):
    """Upload a document from a URL."""
    result = await document_service.upload_from_url(url)
    return result


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    document_service: DocumentService = Depends(get_document_service),
):
    """List all uploaded documents with pagination."""
    result = await document_service.list_documents(
        page=page,
        page_size=page_size,
        status=status,
    )
    return result


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
):
    """Get a specific document by ID."""
    result = await document_service.get_document(document_id)
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    return result


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
):
    """Delete a document and its associated data."""
    success = await document_service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully"}


@router.post("/{document_id}/reprocess")
async def reprocess_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
):
    """Reprocess a document (re-extract entities, rebuild graph)."""
    result = await document_service.reprocess_document(document_id)
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document reprocessing started", "document_id": document_id}
