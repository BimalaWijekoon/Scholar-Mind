"""
Graph State - State management for LangGraph agents
"""

from typing import List, Dict, Any, Optional, TypedDict, Annotated
from dataclasses import dataclass, field
from enum import Enum
import operator


class NodeType(str, Enum):
    """Types of nodes in the agent graph."""
    START = "start"
    ROUTER = "router"
    TOOL = "tool"
    LLM = "llm"
    HUMAN = "human"
    END = "end"


class MessageType(str, Enum):
    """Types of messages."""
    HUMAN = "human"
    AI = "ai"
    SYSTEM = "system"
    TOOL = "tool"
    FUNCTION = "function"


@dataclass
class Message:
    """Represents a message in the conversation."""
    type: MessageType
    content: str
    metadata: Dict = field(default_factory=dict)
    tool_calls: List[Dict] = field(default_factory=list)


@dataclass
class ToolResult:
    """Result from a tool execution."""
    tool_name: str
    result: Any
    success: bool
    error: Optional[str] = None


class GraphState(TypedDict, total=False):
    """
    State for LangGraph agents.
    
    This class defines the structure of state that flows through
    the agent graph.
    """
    # Core state
    messages: Annotated[List[Dict], operator.add]
    query: str
    
    # Retrieval state
    documents: List[Dict]
    graph_entities: List[Dict]
    graph_relations: List[Dict]
    
    # Processing state
    current_node: str
    tool_results: List[Dict]
    intermediate_steps: List[Dict]
    
    # Output state
    response: str
    citations: List[Dict]
    confidence: float
    
    # Control state
    next_action: str
    should_continue: bool
    iteration_count: int
    max_iterations: int
    error: Optional[str]


def create_initial_state(query: str, **kwargs) -> GraphState:
    """
    Create an initial graph state.
    
    Args:
        query: User query
        **kwargs: Additional state values
        
    Returns:
        Initial GraphState
    """
    state: GraphState = {
        "messages": [{"type": "human", "content": query}],
        "query": query,
        "documents": [],
        "graph_entities": [],
        "graph_relations": [],
        "current_node": NodeType.START.value,
        "tool_results": [],
        "intermediate_steps": [],
        "response": "",
        "citations": [],
        "confidence": 0.0,
        "next_action": "",
        "should_continue": True,
        "iteration_count": 0,
        "max_iterations": 10,
        "error": None,
    }
    
    # Override with provided values
    state.update(kwargs)
    
    return state


def add_message(state: GraphState, message_type: str, content: str, **metadata) -> GraphState:
    """
    Add a message to the state.
    
    Args:
        state: Current state
        message_type: Type of message
        content: Message content
        **metadata: Additional metadata
        
    Returns:
        Updated state
    """
    new_message = {
        "type": message_type,
        "content": content,
        **metadata,
    }
    
    state["messages"] = state.get("messages", []) + [new_message]
    return state


def add_document(state: GraphState, document: Dict) -> GraphState:
    """
    Add a document to the state.
    
    Args:
        state: Current state
        document: Document to add
        
    Returns:
        Updated state
    """
    state["documents"] = state.get("documents", []) + [document]
    return state


def add_tool_result(state: GraphState, tool_name: str, result: Any, success: bool = True) -> GraphState:
    """
    Add a tool result to the state.
    
    Args:
        state: Current state
        tool_name: Name of the tool
        result: Tool result
        success: Whether execution was successful
        
    Returns:
        Updated state
    """
    tool_result = {
        "tool_name": tool_name,
        "result": result,
        "success": success,
    }
    
    state["tool_results"] = state.get("tool_results", []) + [tool_result]
    return state


def set_response(state: GraphState, response: str, confidence: float = 0.0) -> GraphState:
    """
    Set the final response.
    
    Args:
        state: Current state
        response: Response text
        confidence: Confidence score
        
    Returns:
        Updated state
    """
    state["response"] = response
    state["confidence"] = confidence
    return state


def should_continue(state: GraphState) -> bool:
    """
    Check if the agent should continue.
    
    Args:
        state: Current state
        
    Returns:
        True if should continue
    """
    # Check for explicit stop
    if not state.get("should_continue", True):
        return False
    
    # Check for max iterations
    if state.get("iteration_count", 0) >= state.get("max_iterations", 10):
        return False
    
    # Check for error
    if state.get("error"):
        return False
    
    # Check if response is ready
    if state.get("response") and state.get("current_node") == NodeType.END.value:
        return False
    
    return True


def increment_iteration(state: GraphState) -> GraphState:
    """Increment the iteration counter."""
    state["iteration_count"] = state.get("iteration_count", 0) + 1
    return state


def set_error(state: GraphState, error: str) -> GraphState:
    """Set an error state."""
    state["error"] = error
    state["should_continue"] = False
    return state


def get_last_message(state: GraphState) -> Optional[Dict]:
    """Get the last message from state."""
    messages = state.get("messages", [])
    return messages[-1] if messages else None


def get_context_summary(state: GraphState) -> str:
    """
    Get a summary of the current context.
    
    Args:
        state: Current state
        
    Returns:
        Context summary string
    """
    parts = []
    
    # Documents
    docs = state.get("documents", [])
    if docs:
        parts.append(f"Documents: {len(docs)} retrieved")
        for i, doc in enumerate(docs[:3]):
            text = doc.get("text", "")[:100]
            parts.append(f"  [{i+1}] {text}...")
    
    # Graph entities
    entities = state.get("graph_entities", [])
    if entities:
        parts.append(f"Entities: {len(entities)} found")
    
    # Graph relations
    relations = state.get("graph_relations", [])
    if relations:
        parts.append(f"Relations: {len(relations)} found")
    
    # Tool results
    tool_results = state.get("tool_results", [])
    if tool_results:
        parts.append(f"Tool executions: {len(tool_results)}")
    
    return "\n".join(parts) if parts else "No context available"
