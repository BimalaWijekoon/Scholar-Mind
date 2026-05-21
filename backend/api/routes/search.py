"""
Search API Routes
"""

from typing import List, Optional
from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel

from backend.api.dependencies import get_query_service
from backend.services.query_service import QueryService


router = APIRouter()


class SearchResult(BaseModel):
    """Search result model."""
    id: str
    document_id: str
    document_title: str
    text: str
    page: Optional[int] = None
    score: float
    highlights: List[str]


class SearchResponse(BaseModel):
    """Search response model."""
    results: List[SearchResult]
    total: int
    query: str


class SemanticSearchRequest(BaseModel):
    """Semantic search request model."""
    query: str
    document_ids: Optional[List[str]] = None
    top_k: int = 10
    threshold: float = 0.5


@router.get("/text", response_model=SearchResponse)
async def text_search(
    q: str = Query(..., min_length=1),
    document_ids: Optional[List[str]] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    query_service: QueryService = Depends(get_query_service),
):
    """
    Full-text search across documents.
    
    Searches through document content using keyword matching.
    """
    result = await query_service.text_search(
        query=q,
        document_ids=document_ids,
        page=page,
        page_size=page_size,
    )
    return result


@router.post("/semantic", response_model=SearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    query_service: QueryService = Depends(get_query_service),
):
    """
    Semantic search using vector embeddings.
    
    Finds semantically similar content even if keywords don't match.
    """
    result = await query_service.semantic_search(
        query=request.query,
        document_ids=request.document_ids,
        top_k=request.top_k,
        threshold=request.threshold,
    )
    return result


@router.get("/hybrid", response_model=SearchResponse)
async def hybrid_search(
    q: str = Query(..., min_length=1),
    document_ids: Optional[List[str]] = Query(None),
    top_k: int = Query(10, ge=1, le=50),
    alpha: float = Query(0.5, ge=0.0, le=1.0),
    query_service: QueryService = Depends(get_query_service),
):
    """
    Hybrid search combining text and semantic search.
    
    Alpha controls the balance: 0 = pure text, 1 = pure semantic.
    """
    result = await query_service.hybrid_search(
        query=q,
        document_ids=document_ids,
        top_k=top_k,
        alpha=alpha,
    )
    return result


@router.get("/similar/{document_id}")
async def find_similar_documents(
    document_id: str,
    top_k: int = Query(5, ge=1, le=20),
    query_service: QueryService = Depends(get_query_service),
):
    """Find documents similar to a given document."""
    result = await query_service.find_similar_documents(
        document_id=document_id,
        top_k=top_k,
    )
    return result


@router.get("/entities")
async def search_entities(
    q: str = Query(..., min_length=1),
    entity_type: Optional[str] = None,
    top_k: int = Query(10, ge=1, le=50),
    query_service: QueryService = Depends(get_query_service),
):
    """Search for entities by name or properties."""
    result = await query_service.search_entities(
        query=q,
        entity_type=entity_type,
        top_k=top_k,
    )
    return result
