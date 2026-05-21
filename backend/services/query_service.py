"""
Query Service - Handle question answering and search
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Result of a query."""
    answer: str
    sources: List[Dict]
    confidence: float
    metadata: Dict


@dataclass
class ChatMessage:
    """Chat message."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict = field(default_factory=dict)


class QueryService:
    """
    Service for question answering and search.
    
    Handles:
    - Question answering with RAG
    - Chat conversations
    - Multi-hop reasoning
    - Source citation
    """
    
    def __init__(
        self,
        llm=None,
        retriever=None,
        reranker=None,
        graph_query_engine=None,
        research_agent=None,
    ):
        """
        Initialize the query service.
        
        Args:
            llm: Language model
            retriever: Hybrid retriever
            reranker: Reranker for improving results
            graph_query_engine: Knowledge graph query engine
            research_agent: Research agent for complex queries
        """
        self.llm = llm
        self.retriever = retriever
        self.reranker = reranker
        self.graph_query_engine = graph_query_engine
        self.research_agent = research_agent
        
        # Conversation history per session
        self._conversations: Dict[str, List[ChatMessage]] = {}
    
    async def ask(
        self,
        question: str,
        session_id: Optional[str] = None,
        use_agent: bool = False,
    ) -> QueryResult:
        """
        Answer a question using RAG.
        
        Args:
            question: User question
            session_id: Optional session for context
            use_agent: Whether to use the research agent
            
        Returns:
            QueryResult with answer and sources
        """
        logger.info(f"Processing question: {question[:100]}...")
        
        # Use agent for complex queries
        if use_agent and self.research_agent:
            return await self._ask_with_agent(question, session_id)
        
        # Standard RAG pipeline
        return await self._ask_with_rag(question, session_id)
    
    async def _ask_with_rag(
        self,
        question: str,
        session_id: Optional[str],
    ) -> QueryResult:
        """Answer using standard RAG."""
        sources = []
        
        # Retrieve relevant documents
        if self.retriever:
            results = self.retriever.retrieve(question, k=10)
            
            # Rerank if available
            if self.reranker and results:
                docs = [{"id": r.id, "text": r.text, "score": r.score} for r in results]
                reranked = self.reranker.rerank(question, docs, top_k=5)
                sources = [
                    {
                        "id": r.id,
                        "text": r.text[:500],
                        "score": r.rerank_score,
                    }
                    for r in reranked
                ]
            else:
                sources = [
                    {
                        "id": r.id,
                        "text": r.text[:500],
                        "score": r.score,
                    }
                    for r in results[:5]
                ]
        
        # Get graph context
        graph_context = ""
        if self.graph_query_engine:
            try:
                graph_result = await self.graph_query_engine.query(
                    question,
                    parameters={"limit": 5},
                )
                if graph_result.results:
                    graph_context = "\n".join(str(r) for r in graph_result.results[:3])
            except Exception as e:
                logger.warning(f"Graph query failed: {e}")
        
        # Generate answer
        if self.llm:
            answer = await self._generate_answer(question, sources, graph_context, session_id)
        else:
            # Fallback: return sources as answer
            if sources:
                answer = "Based on the retrieved documents:\n\n"
                for i, src in enumerate(sources, 1):
                    answer += f"{i}. {src['text'][:200]}...\n\n"
            else:
                answer = "I couldn't find relevant information to answer your question."
        
        # Store in conversation
        if session_id:
            self._add_to_conversation(session_id, "user", question)
            self._add_to_conversation(session_id, "assistant", answer)
        
        return QueryResult(
            answer=answer,
            sources=sources,
            confidence=0.8 if sources else 0.3,
            metadata={"graph_context": graph_context} if graph_context else {},
        )
    
    async def _ask_with_agent(
        self,
        question: str,
        session_id: Optional[str],
    ) -> QueryResult:
        """Answer using research agent."""
        context = []
        
        # Get conversation history
        if session_id and session_id in self._conversations:
            context = [
                {"role": msg.role, "content": msg.content}
                for msg in self._conversations[session_id][-5:]
            ]
        
        # Run agent
        result = await self.research_agent.run(question, context=context)
        
        # Store in conversation
        if session_id:
            self._add_to_conversation(session_id, "user", question)
            self._add_to_conversation(session_id, "assistant", result["response"])
        
        return QueryResult(
            answer=result["response"],
            sources=result.get("sources", []),
            confidence=0.85,
            metadata={
                "analysis": result.get("analysis", ""),
                "iterations": result.get("iterations", 0),
            },
        )
    
    async def _generate_answer(
        self,
        question: str,
        sources: List[Dict],
        graph_context: str,
        session_id: Optional[str],
    ) -> str:
        """Generate answer using LLM."""
        # Build context
        context_parts = []
        
        if sources:
            context_parts.append("Retrieved Information:")
            for i, src in enumerate(sources, 1):
                context_parts.append(f"[{i}] {src['text']}")
        
        if graph_context:
            context_parts.append(f"\nKnowledge Graph Context:\n{graph_context}")
        
        context = "\n\n".join(context_parts)
        
        # Build conversation history
        history = ""
        if session_id and session_id in self._conversations:
            history_msgs = self._conversations[session_id][-3:]
            history = "\n".join(f"{m.role}: {m.content}" for m in history_msgs)
        
        # Build prompt
        prompt = f"""Answer the question based on the provided context. 
If the context doesn't contain enough information, acknowledge the limitation.
Always cite sources when referencing specific information.

Context:
{context}

{f"Previous conversation:{chr(10)}{history}{chr(10)}" if history else ""}

Question: {question}

Answer:"""
        
        # Generate
        try:
            from langchain_core.messages import HumanMessage
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return "I apologize, but I encountered an error generating a response."
    
    async def chat(
        self,
        message: str,
        session_id: str = None,
        conversation_history: List = None,
        document_ids: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle a chat message with conversation context.
        
        Args:
            message: User message
            session_id: Session ID for conversation tracking
            conversation_history: List of previous messages
            document_ids: Optional document filter
            
        Returns:
            Chat response dict
        """
        # Check if LLM is configured
        if not self.llm:
            return {
                "response": "I'm sorry, but the AI assistant is not configured. Please set your GOOGLE_API_KEY in the .env file to enable chat functionality.",
                "citations": [],
                "suggested_questions": [
                    "How do I configure the API key?",
                    "What documents have been uploaded?",
                ],
            }
        
        try:
            result = await self.ask(message, session_id=session_id, use_agent=False)
            return {
                "response": result.answer,
                "citations": [
                    {
                        "document_id": s.get("document_id", ""),
                        "document_title": s.get("title", "Unknown"),
                        "page": s.get("page"),
                        "text": s.get("text", ""),
                        "relevance_score": s.get("score", 0.0),
                    }
                    for s in result.sources
                ],
                "suggested_questions": [
                    "Can you explain more about this topic?",
                    "What are the key concepts mentioned?",
                    "Are there any related documents?",
                ],
            }
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return {
                "response": f"I encountered an error processing your request. Please try again.",
                "citations": [],
                "suggested_questions": [],
            }
    
    async def answer_question(
        self,
        question: str,
        document_ids: List[str] = None,
        use_graph: bool = True,
        max_sources: int = 5,
    ) -> Dict[str, Any]:
        """
        Answer a question for the API route.
        
        Args:
            question: User question
            document_ids: Optional document filter
            use_graph: Whether to use knowledge graph
            max_sources: Maximum number of sources
            
        Returns:
            Answer response dict
        """
        if not self.llm:
            return {
                "answer": "AI assistant is not configured. Please set GOOGLE_API_KEY in .env file.",
                "citations": [],
                "confidence": 0.0,
                "follow_up_questions": [],
                "reasoning_path": None,
            }
        
        try:
            result = await self.ask(question, use_agent=use_graph)
            return {
                "answer": result.answer,
                "citations": [
                    {
                        "document_id": s.get("document_id", ""),
                        "document_title": s.get("title", "Unknown"),
                        "page": s.get("page"),
                        "text": s.get("text", ""),
                        "relevance_score": s.get("score", 0.0),
                    }
                    for s in result.sources[:max_sources]
                ],
                "confidence": result.confidence,
                "follow_up_questions": [
                    "What are the main findings?",
                    "Can you provide more details?",
                    "How does this relate to other topics?",
                ],
                "reasoning_path": result.metadata.get("reasoning_path"),
            }
        except Exception as e:
            logger.error(f"Answer question error: {e}")
            return {
                "answer": "I encountered an error. Please try again.",
                "citations": [],
                "confidence": 0.0,
                "follow_up_questions": [],
                "reasoning_path": None,
            }
    
    async def multi_hop_reasoning(
        self,
        question: str,
        max_hops: int = 3,
    ) -> Dict[str, Any]:
        """Perform multi-hop reasoning for complex questions."""
        result = await self.ask(question, use_agent=True)
        return {
            "answer": result.answer,
            "reasoning_path": result.metadata.get("reasoning_path", []),
            "sources": result.sources,
            "hops_taken": min(max_hops, len(result.metadata.get("reasoning_path", []))),
        }
    
    async def compare_documents(
        self,
        document_ids: List[str],
        aspect: str = None,
    ) -> Dict[str, Any]:
        """Compare multiple documents."""
        return {
            "comparison": "Document comparison feature requires documents to be processed first.",
            "documents": document_ids,
            "aspect": aspect or "general",
            "similarities": [],
            "differences": [],
        }
    
    def _add_to_conversation(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        """Add message to conversation history."""
        if session_id not in self._conversations:
            self._conversations[session_id] = []
        
        self._conversations[session_id].append(ChatMessage(
            role=role,
            content=content,
        ))
        
        # Limit history
        if len(self._conversations[session_id]) > 50:
            self._conversations[session_id] = self._conversations[session_id][-50:]
    
    def get_conversation(self, session_id: str) -> List[ChatMessage]:
        """Get conversation history."""
        return self._conversations.get(session_id, [])
    
    def clear_conversation(self, session_id: str) -> None:
        """Clear conversation history."""
        if session_id in self._conversations:
            del self._conversations[session_id]
    
    async def multi_hop(
        self,
        question: str,
        max_hops: int = 3,
    ) -> QueryResult:
        """
        Perform multi-hop reasoning.
        
        Args:
            question: Complex question requiring multiple reasoning steps
            max_hops: Maximum reasoning hops
            
        Returns:
            QueryResult with multi-hop answer
        """
        # Use agent with multi-hop reasoning
        if self.research_agent:
            result = await self.research_agent.run(question)
            return QueryResult(
                answer=result["response"],
                sources=result.get("sources", []),
                confidence=0.8,
                metadata={"hops": result.get("iterations", 1)},
            )
        
        # Fallback to standard RAG
        return await self.ask(question)
