"""
Question Answering API Routes
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from backend.api.dependencies import get_query_service
from backend.services.query_service import QueryService


router = APIRouter()


class Citation(BaseModel):
    """Citation model."""
    document_id: str
    document_title: str
    page: Optional[int] = None
    text: str
    relevance_score: float


class QueryRequest(BaseModel):
    """Query request model."""
    question: str
    document_ids: Optional[List[str]] = None
    use_graph: bool = True
    max_sources: int = 5


class QueryResponse(BaseModel):
    """Query response model."""
    answer: str
    citations: List[Citation]
    confidence: float
    follow_up_questions: List[str]
    reasoning_path: Optional[List[str]] = None


class ConversationMessage(BaseModel):
    """Conversation message model."""
    role: str  # "user" or "assistant"
    content: str
    citations: Optional[List[Citation]] = None


class ChatRequest(BaseModel):
    """Chat request with conversation history."""
    message: str
    conversation_history: List[ConversationMessage] = []
    document_ids: Optional[List[str]] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    citations: List[Citation]
    suggested_questions: List[str]


@router.post("/ask", response_model=QueryResponse)
async def ask_question(
    request: QueryRequest,
    query_service: QueryService = Depends(get_query_service),
):
    """
    Ask a research question and get an AI-powered answer with citations.
    
    The system uses GraphRAG to:
    1. Search the vector store for relevant chunks
    2. Traverse the knowledge graph for related entities
    3. Combine information from multiple sources
    4. Generate a comprehensive answer with citations
    """
    result = await query_service.answer_question(
        question=request.question,
        document_ids=request.document_ids,
        use_graph=request.use_graph,
        max_sources=request.max_sources,
    )
    return result


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    query_service: QueryService = Depends(get_query_service),
):
    """
    Have a conversation about your research documents.
    
    Maintains conversation context and can handle follow-up questions.
    """
    result = await query_service.chat(
        message=request.message,
        conversation_history=request.conversation_history,
        document_ids=request.document_ids,
    )
    return result


@router.post("/multi-hop")
async def multi_hop_query(
    question: str,
    max_hops: int = 3,
    query_service: QueryService = Depends(get_query_service),
):
    """
    Perform multi-hop reasoning across documents.
    
    Useful for questions like:
    - "How does X relate to Y through Z?"
    - "What methods does author A use that are similar to author B's work?"
    """
    result = await query_service.multi_hop_reasoning(
        question=question,
        max_hops=max_hops,
    )
    return result


@router.post("/compare")
async def compare_documents(
    document_ids: List[str],
    aspect: Optional[str] = None,
    query_service: QueryService = Depends(get_query_service),
):
    """
    Compare multiple documents on specific aspects.
    
    Can compare methods, results, conclusions, etc.
    """
    if len(document_ids) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 documents required for comparison",
        )
    
    result = await query_service.compare_documents(
        document_ids=document_ids,
        aspect=aspect,
    )
    return result
