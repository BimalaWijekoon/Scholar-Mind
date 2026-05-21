"""
Search Tool - Document search tool for agents
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Result from search."""
    id: str
    text: str
    score: float
    title: Optional[str]
    metadata: Dict


class SearchTool:
    """
    Search tool for agent document retrieval.
    
    Provides:
    - Semantic search
    - Keyword search
    - Hybrid search
    - Filtered search
    """
    
    name = "search"
    description = """Search the document knowledge base for relevant information.
    
    Use this tool when you need to find documents related to a topic, concept, or question.
    The tool supports natural language queries and will return the most relevant documents.
    
    Input: A search query string
    Output: List of relevant document excerpts with metadata"""
    
    def __init__(
        self,
        retriever: Optional[Any] = None,
        embeddings_manager: Optional[Any] = None,
        max_results: int = 5,
    ):
        """
        Initialize the search tool.
        
        Args:
            retriever: Hybrid retriever instance
            embeddings_manager: Embeddings manager for semantic search
            max_results: Maximum number of results to return
        """
        self.retriever = retriever
        self.embeddings_manager = embeddings_manager
        self.max_results = max_results
    
    def run(self, query: str, **kwargs) -> List[SearchResult]:
        """
        Execute a search query.
        
        Args:
            query: Search query
            **kwargs: Additional parameters
            
        Returns:
            List of search results
        """
        if not self.retriever:
            return []
        
        # Get search parameters
        k = kwargs.get("k", self.max_results)
        search_type = kwargs.get("search_type", "hybrid")
        filters = kwargs.get("filters", None)
        
        # Perform search
        try:
            from backend.core.retrieval.hybrid_retriever import RetrievalMode
            
            mode_map = {
                "semantic": RetrievalMode.SEMANTIC,
                "keyword": RetrievalMode.KEYWORD,
                "hybrid": RetrievalMode.HYBRID,
            }
            
            mode = mode_map.get(search_type, RetrievalMode.HYBRID)
            
            results = self.retriever.retrieve(
                query=query,
                k=k,
                mode=mode,
                filter_metadata=filters,
            )
            
            return [
                SearchResult(
                    id=r.id,
                    text=r.text,
                    score=r.score,
                    title=r.metadata.get("title"),
                    metadata=r.metadata,
                )
                for r in results
            ]
        except Exception as e:
            return []
    
    async def arun(self, query: str, **kwargs) -> List[SearchResult]:
        """Async version of run."""
        return self.run(query, **kwargs)
    
    def format_results(self, results: List[SearchResult]) -> str:
        """
        Format results for LLM consumption.
        
        Args:
            results: Search results
            
        Returns:
            Formatted string
        """
        if not results:
            return "No relevant documents found."
        
        parts = []
        for i, result in enumerate(results, 1):
            title = result.title or "Untitled"
            text = result.text[:500] + "..." if len(result.text) > 500 else result.text
            score = f"{result.score:.3f}"
            
            parts.append(f"[{i}] {title} (relevance: {score})\n{text}\n")
        
        return "\n".join(parts)
    
    def get_schema(self) -> Dict:
        """Get tool schema for function calling."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query",
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["semantic", "keyword", "hybrid"],
                        "description": "Type of search to perform",
                        "default": "hybrid",
                    },
                    "k": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        }
