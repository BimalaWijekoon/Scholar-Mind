"""
Analyzer Tool - Document analysis tool for agents
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class AnalysisResult:
    """Result from analysis."""
    summary: str
    key_points: List[str]
    entities: List[Dict]
    topics: List[str]
    sentiment: Optional[str]
    metadata: Dict


class AnalyzerTool:
    """
    Document analysis tool for agents.
    
    Provides:
    - Text summarization
    - Key point extraction
    - Entity recognition
    - Topic identification
    """
    
    name = "analyze"
    description = """Analyze documents or text for insights and information extraction.
    
    Use this tool to:
    - Summarize long documents
    - Extract key points and findings
    - Identify entities and topics
    - Compare multiple documents
    
    Input: Text to analyze or document IDs
    Output: Analysis with summary, key points, and extracted information"""
    
    def __init__(
        self,
        llm: Optional[Any] = None,
        entity_extractor: Optional[Any] = None,
    ):
        """
        Initialize the analyzer tool.
        
        Args:
            llm: Language model for analysis
            entity_extractor: Entity extractor instance
        """
        self.llm = llm
        self.entity_extractor = entity_extractor
    
    def run(self, text: str, **kwargs) -> AnalysisResult:
        """
        Analyze text.
        
        Args:
            text: Text to analyze
            **kwargs: Additional parameters
            
        Returns:
            Analysis results
        """
        analysis_type = kwargs.get("analysis_type", "full")
        
        if analysis_type == "summarize":
            return self._summarize(text)
        elif analysis_type == "extract_key_points":
            return self._extract_key_points(text)
        elif analysis_type == "extract_entities":
            return self._extract_entities(text)
        elif analysis_type == "identify_topics":
            return self._identify_topics(text)
        else:
            return self._full_analysis(text)
    
    def _summarize(self, text: str) -> AnalysisResult:
        """Summarize text."""
        summary = ""
        
        if self.llm:
            try:
                from langchain_core.messages import HumanMessage
                
                response = self.llm.invoke([
                    HumanMessage(content=f"Summarize the following text concisely:\n\n{text[:4000]}")
                ])
                summary = response.content
            except Exception:
                # Fallback: first few sentences
                sentences = text.split('. ')
                summary = '. '.join(sentences[:3]) + '.'
        else:
            sentences = text.split('. ')
            summary = '. '.join(sentences[:3]) + '.'
        
        return AnalysisResult(
            summary=summary,
            key_points=[],
            entities=[],
            topics=[],
            sentiment=None,
            metadata={"analysis_type": "summarize"},
        )
    
    def _extract_key_points(self, text: str) -> AnalysisResult:
        """Extract key points from text."""
        key_points = []
        
        if self.llm:
            try:
                from langchain_core.messages import HumanMessage
                
                response = self.llm.invoke([
                    HumanMessage(content=f"Extract 5-7 key points from this text. Format as a bulleted list:\n\n{text[:4000]}")
                ])
                
                # Parse bullet points
                lines = response.content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith(('- ', '• ', '* ', '1.', '2.', '3.', '4.', '5.', '6.', '7.')):
                        point = line.lstrip('-•* 0123456789.').strip()
                        if point:
                            key_points.append(point)
            except Exception:
                pass
        
        return AnalysisResult(
            summary="",
            key_points=key_points,
            entities=[],
            topics=[],
            sentiment=None,
            metadata={"analysis_type": "extract_key_points"},
        )
    
    def _extract_entities(self, text: str) -> AnalysisResult:
        """Extract entities from text."""
        entities = []
        
        if self.entity_extractor:
            try:
                extracted = self.entity_extractor.extract(text)
                entities = [
                    {
                        "text": e.text,
                        "type": e.entity_type,
                        "confidence": e.confidence,
                    }
                    for e in extracted
                ]
            except Exception:
                pass
        
        return AnalysisResult(
            summary="",
            key_points=[],
            entities=entities,
            topics=[],
            sentiment=None,
            metadata={"analysis_type": "extract_entities"},
        )
    
    def _identify_topics(self, text: str) -> AnalysisResult:
        """Identify topics in text."""
        topics = []
        
        if self.llm:
            try:
                from langchain_core.messages import HumanMessage
                
                response = self.llm.invoke([
                    HumanMessage(content=f"Identify the main topics discussed in this text. List 3-5 topics:\n\n{text[:4000]}")
                ])
                
                lines = response.content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith(('- ', '• ', '* ', '1.', '2.', '3.', '4.', '5.')):
                        topic = line.lstrip('-•* 0123456789.').strip()
                        if topic:
                            topics.append(topic)
            except Exception:
                pass
        
        return AnalysisResult(
            summary="",
            key_points=[],
            entities=[],
            topics=topics,
            sentiment=None,
            metadata={"analysis_type": "identify_topics"},
        )
    
    def _full_analysis(self, text: str) -> AnalysisResult:
        """Perform full analysis."""
        # Combine all analysis types
        summary_result = self._summarize(text)
        key_points_result = self._extract_key_points(text)
        entities_result = self._extract_entities(text)
        topics_result = self._identify_topics(text)
        
        return AnalysisResult(
            summary=summary_result.summary,
            key_points=key_points_result.key_points,
            entities=entities_result.entities,
            topics=topics_result.topics,
            sentiment=None,
            metadata={"analysis_type": "full"},
        )
    
    async def arun(self, text: str, **kwargs) -> AnalysisResult:
        """Async version of run."""
        return self.run(text, **kwargs)
    
    def format_results(self, results: AnalysisResult) -> str:
        """Format results for LLM consumption."""
        parts = []
        
        if results.summary:
            parts.append(f"Summary:\n{results.summary}")
        
        if results.key_points:
            parts.append("\nKey Points:")
            for point in results.key_points:
                parts.append(f"  • {point}")
        
        if results.entities:
            parts.append("\nEntities:")
            for entity in results.entities[:10]:
                parts.append(f"  - {entity['text']} ({entity['type']})")
        
        if results.topics:
            parts.append("\nTopics:")
            for topic in results.topics:
                parts.append(f"  - {topic}")
        
        if not parts:
            return "Analysis could not be completed."
        
        return "\n".join(parts)
    
    def get_schema(self) -> Dict:
        """Get tool schema for function calling."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to analyze",
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": ["full", "summarize", "extract_key_points", "extract_entities", "identify_topics"],
                        "description": "Type of analysis to perform",
                        "default": "full",
                    },
                },
                "required": ["text"],
            },
        }
