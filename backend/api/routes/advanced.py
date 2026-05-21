"""
Advanced Features API Routes

Endpoints for advanced research features:
- Claim extraction
- Contradiction detection
- Paper recommendations
- Research question generation
- Duplicate detection
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field


router = APIRouter()


# ============= Request/Response Models =============

class ClaimRequest(BaseModel):
    """Request for claim extraction."""
    text: str = Field(..., description="Text to extract claims from")
    top_k: int = Field(10, ge=1, le=50, description="Number of claims to return")


class ClaimResponse(BaseModel):
    """Extracted claim."""
    text: str
    type: str
    confidence: float
    entities: List[str]
    metrics: List[dict]
    verifiable: bool
    evidence_needed: List[str]


class ContradictionRequest(BaseModel):
    """Request for contradiction detection."""
    document_id_1: str = Field(..., description="First document ID")
    document_id_2: str = Field(..., description="Second document ID")


class ContradictionResponse(BaseModel):
    """Detected contradiction."""
    claim1: str
    claim2: str
    source1: str
    source2: str
    type: str
    severity: str
    confidence: float
    explanation: str
    shared_entities: List[str]
    resolution_suggestions: List[str]


class RecommendationResponse(BaseModel):
    """Paper recommendation."""
    document_id: str
    title: str
    score: float
    type: str
    reasons: List[str]
    shared_entities: List[str]
    shared_authors: List[str]
    explanation: str


class ResearchQuestionResponse(BaseModel):
    """Generated research question."""
    question: str
    type: str
    relevance_score: float
    source_concepts: List[str]
    rationale: str
    suggested_methods: List[str]


class DuplicateResponse(BaseModel):
    """Duplicate detection result."""
    document_id: str
    match_document_id: str
    similarity_level: str
    similarity_score: float
    matching_sections: List[str]
    differences: List[str]
    recommendation: str


# ============= Claim Extraction =============

@router.post("/claims/extract", response_model=List[ClaimResponse])
async def extract_claims(request: ClaimRequest):
    """
    Extract verifiable claims from text.
    
    Identifies sentences that make specific, verifiable claims such as:
    - Performance claims (e.g., "achieves 95% accuracy")
    - Comparison claims (e.g., "outperforms BERT")
    - Contribution claims (e.g., "we propose a novel approach")
    """
    try:
        from backend.ml.claim_extractor import extract_claims as do_extract
        
        claims = do_extract(request.text, top_k=request.top_k)
        return claims
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Claim extraction failed: {str(e)}")


@router.get("/claims/document/{document_id}", response_model=List[ClaimResponse])
async def get_document_claims(
    document_id: str,
    top_k: int = Query(10, ge=1, le=50),
):
    """Get claims from a specific document."""
    try:
        from backend.services.document_service import DocumentService
        from backend.ml.claim_extractor import extract_claims as do_extract
        
        # Get document text
        doc_service = DocumentService()
        doc = await doc_service.get_document(document_id)
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Extract claims
        text = doc.get('text', doc.get('content', ''))
        claims = do_extract(text, top_k=top_k)
        
        return claims
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get claims: {str(e)}")


# ============= Contradiction Detection =============

@router.post("/contradictions/detect", response_model=List[ContradictionResponse])
async def detect_contradictions(request: ContradictionRequest):
    """
    Detect contradictions between two documents.
    
    Identifies conflicting claims such as:
    - Numerical discrepancies
    - Opposing conclusions
    - Conflicting methodological claims
    """
    try:
        from backend.services.document_service import DocumentService
        from backend.ml.claim_extractor import extract_claims
        from backend.ml.contradiction_detector import detect_contradictions as do_detect
        
        doc_service = DocumentService()
        
        # Get documents
        doc1 = await doc_service.get_document(request.document_id_1)
        doc2 = await doc_service.get_document(request.document_id_2)
        
        if not doc1:
            raise HTTPException(status_code=404, detail="Document 1 not found")
        if not doc2:
            raise HTTPException(status_code=404, detail="Document 2 not found")
        
        # Extract claims from both documents
        text1 = doc1.get('text', doc1.get('content', ''))
        text2 = doc2.get('text', doc2.get('content', ''))
        
        claims1 = extract_claims(text1, top_k=20)
        claims2 = extract_claims(text2, top_k=20)
        
        # Detect contradictions
        contradictions = do_detect(
            claims1, claims2,
            source1=doc1.get('title', request.document_id_1),
            source2=doc2.get('title', request.document_id_2),
        )
        
        return contradictions
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Contradiction detection failed: {str(e)}")


@router.post("/contradictions/claims")
async def detect_claim_contradictions(
    claims1: List[dict] = Body(..., description="First set of claims"),
    claims2: List[dict] = Body(..., description="Second set of claims"),
    source1: str = Body("Source 1", description="Name of first source"),
    source2: str = Body("Source 2", description="Name of second source"),
):
    """Detect contradictions between two sets of claims directly."""
    try:
        from backend.ml.contradiction_detector import detect_contradictions as do_detect
        
        contradictions = do_detect(claims1, claims2, source1, source2)
        return contradictions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


# ============= Paper Recommendations =============

@router.get("/recommendations/{document_id}", response_model=List[RecommendationResponse])
async def get_recommendations(
    document_id: str,
    top_k: int = Query(10, ge=1, le=50),
):
    """
    Get paper recommendations for a document.
    
    Recommendations are based on:
    - Content similarity
    - Shared topics/entities
    - Citation relationships
    - Author overlap
    - Knowledge graph connections
    """
    try:
        from backend.ml.paper_recommender import get_recommendations as do_recommend
        
        recommendations = await do_recommend(document_id, top_k=top_k)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.post("/recommendations/query")
async def get_query_recommendations(
    query: str = Body(..., embed=True, description="Search query"),
    top_k: int = Query(10, ge=1, le=50),
):
    """Get paper recommendations based on a search query."""
    try:
        from backend.ml.paper_recommender import PaperRecommender
        
        recommender = PaperRecommender()
        recommendations = await recommender.recommend_for_query(query, top_k=top_k)
        
        return [
            {
                "document_id": r.document_id,
                "title": r.title,
                "score": r.score,
                "type": r.recommendation_type.value,
                "reasons": r.reasons,
                "shared_entities": r.shared_entities,
                "shared_authors": r.shared_authors,
                "explanation": r.relevance_explanation,
            }
            for r in recommendations
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


# ============= Research Question Generation =============

@router.post("/questions/generate", response_model=List[ResearchQuestionResponse])
async def generate_research_questions(
    concepts: List[str] = Body(..., description="Key concepts to base questions on"),
    num_questions: int = Body(10, ge=1, le=30),
    question_types: Optional[List[str]] = Body(None, description="Types of questions to generate"),
):
    """
    Generate research questions based on concepts.
    
    Question types:
    - exploratory: What/how questions
    - comparative: Comparing methods
    - causal: Why/cause-effect
    - gap: Addressing research gaps
    - extension: Extending existing work
    - application: Practical applications
    - evaluation: Evaluation methods
    """
    try:
        from backend.ml.question_generator import generate_research_questions as do_generate
        
        questions = await do_generate(
            concepts=concepts,
            num_questions=num_questions,
        )
        return questions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")


@router.get("/questions/document/{document_id}")
async def generate_document_questions(
    document_id: str,
    num_questions: int = Query(10, ge=1, le=30),
):
    """Generate research questions from a specific document."""
    try:
        from backend.ml.question_generator import ResearchQuestionGenerator
        from backend.services.graph_service import GraphService
        
        generator = ResearchQuestionGenerator(graph_service=GraphService())
        questions = await generator.generate(
            document_id=document_id,
            num_questions=num_questions,
        )
        
        return [
            {
                "question": q.question,
                "type": q.question_type.value,
                "relevance_score": q.relevance_score,
                "source_concepts": q.source_concepts,
                "rationale": q.rationale,
                "suggested_methods": q.suggested_methods,
            }
            for q in questions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")


@router.post("/questions/followup")
async def generate_followup_questions(
    query: str = Body(..., description="Original query"),
    context: Optional[str] = Body(None, description="Optional context"),
    num_questions: int = Body(5, ge=1, le=10),
):
    """Generate follow-up questions based on a query."""
    try:
        from backend.ml.question_generator import ResearchQuestionGenerator
        
        generator = ResearchQuestionGenerator()
        followups = await generator.generate_followup_questions(
            query=query,
            context=context,
            num_questions=num_questions,
        )
        
        return {"followup_questions": followups}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate follow-ups: {str(e)}")


# ============= Duplicate Detection =============

@router.get("/duplicates/{document_id}", response_model=List[DuplicateResponse])
async def detect_duplicates(
    document_id: str,
    min_similarity: float = Query(0.5, ge=0.0, le=1.0),
):
    """
    Detect duplicate and similar documents.
    
    Similarity levels:
    - exact: Identical content
    - near_duplicate: Same content, minor differences
    - highly_similar: Very similar (>80%)
    - similar: Similar content (>65%)
    - related: Related content (>50%)
    """
    try:
        from backend.services.document_service import DocumentService
        from backend.ml.duplicate_detector import detect_duplicates as do_detect
        
        doc_service = DocumentService()
        doc = await doc_service.get_document(document_id)
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        text = doc.get('text', doc.get('content', ''))
        duplicates = await do_detect(
            document_id=document_id,
            document_text=text,
            min_similarity=min_similarity,
        )
        
        return duplicates
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Duplicate detection failed: {str(e)}")


@router.post("/duplicates/batch")
async def detect_batch_duplicates(
    documents: List[dict] = Body(..., description="List of documents with 'id' and 'text'"),
    min_similarity: float = Body(0.7, ge=0.0, le=1.0),
):
    """Detect duplicates within a batch of documents."""
    try:
        from backend.ml.duplicate_detector import detect_duplicates_batch
        
        duplicates = detect_duplicates_batch(
            documents=documents,
            min_similarity=min_similarity,
        )
        
        return duplicates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch detection failed: {str(e)}")


# ============= Combined Analysis =============

@router.get("/analyze/{document_id}")
async def analyze_document(
    document_id: str,
    include_claims: bool = Query(True),
    include_recommendations: bool = Query(True),
    include_duplicates: bool = Query(True),
    include_questions: bool = Query(True),
):
    """
    Comprehensive document analysis.
    
    Returns claims, recommendations, duplicate detection, and research questions.
    """
    try:
        from backend.services.document_service import DocumentService
        
        doc_service = DocumentService()
        doc = await doc_service.get_document(document_id)
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        text = doc.get('text', doc.get('content', ''))
        result = {
            "document_id": document_id,
            "title": doc.get('title', ''),
        }
        
        if include_claims:
            from backend.ml.claim_extractor import extract_claims
            result["claims"] = extract_claims(text, top_k=10)
        
        if include_recommendations:
            from backend.ml.paper_recommender import get_recommendations
            result["recommendations"] = await get_recommendations(document_id, top_k=5)
        
        if include_duplicates:
            from backend.ml.duplicate_detector import detect_duplicates
            result["duplicates"] = await detect_duplicates(document_id, text, min_similarity=0.7)
        
        if include_questions:
            from backend.ml.question_generator import ResearchQuestionGenerator
            generator = ResearchQuestionGenerator()
            questions = await generator.generate(document_id=document_id, num_questions=5)
            result["research_questions"] = [
                {
                    "question": q.question,
                    "type": q.question_type.value,
                    "relevance_score": q.relevance_score,
                }
                for q in questions
            ]
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
