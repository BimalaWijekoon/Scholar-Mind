"""
Research Agent - LangGraph-based agentic research assistant
"""

from typing import List, Dict, Optional, Any, Literal
from dataclasses import dataclass, field
from enum import Enum
import logging

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI


logger = logging.getLogger(__name__)


class AgentAction(str, Enum):
    """Possible agent actions."""
    SEARCH = "search"
    RETRIEVE = "retrieve"
    ANALYZE = "analyze"
    SYNTHESIZE = "synthesize"
    GRAPH_QUERY = "graph_query"
    RESPOND = "respond"


@dataclass
class AgentState:
    """State for the research agent."""
    messages: List[Any] = field(default_factory=list)
    query: str = ""
    context: List[Dict] = field(default_factory=list)
    graph_results: List[Dict] = field(default_factory=list)
    retrieved_docs: List[Dict] = field(default_factory=list)
    analysis: str = ""
    response: str = ""
    next_action: Optional[AgentAction] = None
    iteration: int = 0
    max_iterations: int = 5


class ResearchAgent:
    """
    Research agent using LangGraph for multi-step reasoning.
    
    Capabilities:
    - Document retrieval
    - Knowledge graph queries
    - Multi-hop reasoning
    - Answer synthesis
    """
    
    def __init__(
        self,
        llm: Optional[Any] = None,
        retriever: Optional[Any] = None,
        graph_query_engine: Optional[Any] = None,
        system_prompt: Optional[str] = None,
    ):
        """
        Initialize the research agent.
        
        Args:
            llm: Language model (defaults to Gemini)
            retriever: Document retriever
            graph_query_engine: Knowledge graph query engine
            system_prompt: Custom system prompt
        """
        self.llm = llm or self._init_default_llm()
        self.retriever = retriever
        self.graph_query_engine = graph_query_engine
        
        self.system_prompt = system_prompt or self._default_system_prompt()
        
        # Build the agent graph
        self._graph = self._build_graph()
    
    def _init_default_llm(self):
        """Initialize default LLM (Gemini 2.0 Flash)."""
        try:
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                temperature=0.7,
            )
        except Exception as e:
            logger.warning(f"Could not initialize Gemini: {e}")
            return None
    
    def _default_system_prompt(self) -> str:
        """Get default system prompt."""
        return """You are ScholarMind, an AI research assistant specializing in academic paper analysis.

Your capabilities:
1. Search and retrieve relevant documents from the knowledge base
2. Query the knowledge graph for entities and relationships
3. Perform multi-hop reasoning across documents
4. Synthesize information into coherent answers
5. Generate literature reviews and research summaries

Guidelines:
- Always cite sources when referencing specific papers or findings
- Acknowledge uncertainty when information is incomplete
- Provide balanced perspectives on controversial topics
- Use technical language appropriately based on the query
- Structure complex answers with clear organization

When answering questions:
1. First understand what information is needed
2. Retrieve relevant documents and graph data
3. Analyze and cross-reference information
4. Synthesize a comprehensive answer
5. Include citations and confidence levels"""
    
    def _build_graph(self):
        """Build the LangGraph state machine."""
        try:
            from langgraph.graph import StateGraph, END
            
            # Define the graph
            workflow = StateGraph(AgentState)
            
            # Add nodes
            workflow.add_node("route", self._route_node)
            workflow.add_node("retrieve", self._retrieve_node)
            workflow.add_node("graph_query", self._graph_query_node)
            workflow.add_node("analyze", self._analyze_node)
            workflow.add_node("synthesize", self._synthesize_node)
            workflow.add_node("respond", self._respond_node)
            
            # Add edges
            workflow.set_entry_point("route")
            
            workflow.add_conditional_edges(
                "route",
                self._determine_next_action,
                {
                    AgentAction.RETRIEVE: "retrieve",
                    AgentAction.GRAPH_QUERY: "graph_query",
                    AgentAction.ANALYZE: "analyze",
                    AgentAction.SYNTHESIZE: "synthesize",
                    AgentAction.RESPOND: "respond",
                }
            )
            
            workflow.add_edge("retrieve", "route")
            workflow.add_edge("graph_query", "route")
            workflow.add_edge("analyze", "route")
            workflow.add_edge("synthesize", "respond")
            workflow.add_edge("respond", END)
            
            return workflow.compile()
        except ImportError:
            logger.warning("LangGraph not available, using simple execution")
            return None
    
    def _route_node(self, state: AgentState) -> AgentState:
        """Route to the next action."""
        state.iteration += 1
        
        if state.iteration > state.max_iterations:
            state.next_action = AgentAction.RESPOND
            return state
        
        # Determine next action based on state
        if not state.retrieved_docs and self.retriever:
            state.next_action = AgentAction.RETRIEVE
        elif not state.graph_results and self.graph_query_engine:
            state.next_action = AgentAction.GRAPH_QUERY
        elif not state.analysis and (state.retrieved_docs or state.graph_results):
            state.next_action = AgentAction.ANALYZE
        elif state.analysis and not state.response:
            state.next_action = AgentAction.SYNTHESIZE
        else:
            state.next_action = AgentAction.RESPOND
        
        return state
    
    def _determine_next_action(self, state: AgentState) -> AgentAction:
        """Determine the next action from state."""
        return state.next_action or AgentAction.RESPOND
    
    def _retrieve_node(self, state: AgentState) -> AgentState:
        """Retrieve relevant documents."""
        if self.retriever:
            try:
                results = self.retriever.retrieve(state.query, k=5)
                state.retrieved_docs = [
                    {"id": r.id, "text": r.text, "score": r.score}
                    for r in results
                ]
            except Exception as e:
                logger.error(f"Retrieval error: {e}")
        
        return state
    
    def _graph_query_node(self, state: AgentState) -> AgentState:
        """Query the knowledge graph."""
        if self.graph_query_engine:
            try:
                import asyncio
                
                coro = self.graph_query_engine.query(
                    state.query,
                    parameters={"limit": 10}
                )
                
                # Safe async execution — handle both cases:
                # 1. No running loop (e.g. Celery worker) → create one
                # 2. Running loop (e.g. FastAPI) → use nest_asyncio or thread
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                
                if loop and loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        result = pool.submit(asyncio.run, coro).result()
                else:
                    result = asyncio.run(coro)
                
                state.graph_results = result.results
            except Exception as e:
                logger.error(f"Graph query error: {e}")
        
        return state
    
    def _analyze_node(self, state: AgentState) -> AgentState:
        """Analyze retrieved information."""
        if not self.llm:
            return state
        
        # Prepare context
        context_parts = []
        
        if state.retrieved_docs:
            context_parts.append("Retrieved Documents:")
            for i, doc in enumerate(state.retrieved_docs[:5]):
                context_parts.append(f"\n[{i+1}] {doc['text'][:500]}...")
        
        if state.graph_results:
            context_parts.append("\n\nKnowledge Graph Results:")
            for result in state.graph_results[:5]:
                context_parts.append(f"\n- {result}")
        
        context = "\n".join(context_parts)
        
        # Analyze
        analysis_prompt = f"""Analyze the following information to answer the query.

Query: {state.query}

{context}

Provide a detailed analysis of the relevant information, identifying key findings, 
connections between concepts, and any gaps in the available data."""
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=analysis_prompt),
            ])
            state.analysis = response.content
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            state.analysis = "Analysis could not be completed."
        
        return state
    
    def _synthesize_node(self, state: AgentState) -> AgentState:
        """Synthesize final response."""
        if not self.llm:
            state.response = state.analysis or "Unable to generate response."
            return state
        
        synthesis_prompt = f"""Based on the analysis, provide a comprehensive answer to the query.

Query: {state.query}

Analysis:
{state.analysis}

Provide a well-structured answer that:
1. Directly addresses the query
2. Cites relevant sources
3. Acknowledges any limitations or uncertainties
4. Suggests related topics for further exploration"""
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=synthesis_prompt),
            ])
            state.response = response.content
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            state.response = state.analysis or "Unable to generate response."
        
        return state
    
    def _respond_node(self, state: AgentState) -> AgentState:
        """Finalize response."""
        if not state.response:
            state.response = "I apologize, but I was unable to find sufficient information to answer your question."
        
        return state
    
    async def run(self, query: str, context: Optional[List[Dict]] = None) -> Dict:
        """
        Run the research agent.
        
        Args:
            query: User query
            context: Optional additional context
            
        Returns:
            Response dictionary
        """
        initial_state = AgentState(
            query=query,
            context=context or [],
            messages=[HumanMessage(content=query)],
        )
        
        if self._graph:
            final_state = self._graph.invoke(initial_state)
        else:
            # Simple fallback without LangGraph
            final_state = self._simple_run(initial_state)
        
        return {
            "response": final_state.response,
            "sources": final_state.retrieved_docs,
            "graph_context": final_state.graph_results,
            "analysis": final_state.analysis,
            "iterations": final_state.iteration,
        }
    
    def _simple_run(self, state: AgentState) -> AgentState:
        """Simple execution without LangGraph."""
        state = self._retrieve_node(state)
        state = self._graph_query_node(state)
        state = self._analyze_node(state)
        state = self._synthesize_node(state)
        state = self._respond_node(state)
        return state
    
    def run_sync(self, query: str, context: Optional[List[Dict]] = None) -> Dict:
        """Synchronous version of run."""
        import asyncio
        return asyncio.run(self.run(query, context))
