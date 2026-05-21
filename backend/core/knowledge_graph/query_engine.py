"""
Graph Query Engine - Advanced queries and reasoning over knowledge graphs
"""

from typing import List, Dict, Optional, Any, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import networkx as nx


class QueryType(str, Enum):
    """Types of graph queries."""
    NODE_LOOKUP = "node_lookup"
    RELATIONSHIP_QUERY = "relationship_query"
    PATH_FINDING = "path_finding"
    SUBGRAPH = "subgraph"
    AGGREGATION = "aggregation"
    PATTERN_MATCH = "pattern_match"


@dataclass
class QueryResult:
    """Result of a graph query."""
    query_type: QueryType
    results: List[Dict]
    metadata: Dict
    execution_time_ms: float


class GraphQueryEngine:
    """
    Advanced query engine for knowledge graphs.
    
    Supports:
    - Natural language to Cypher translation
    - Multi-hop reasoning
    - Pattern matching
    - Subgraph extraction
    """
    
    def __init__(self, neo4j_client=None, local_graph: Optional[nx.DiGraph] = None):
        """
        Initialize the query engine.
        
        Args:
            neo4j_client: Optional Neo4j client for database queries
            local_graph: Optional NetworkX graph for local queries
        """
        self.neo4j_client = neo4j_client
        self.local_graph = local_graph or nx.DiGraph()
    
    async def query(
        self,
        query_text: str,
        query_type: Optional[QueryType] = None,
        parameters: Optional[Dict] = None,
    ) -> QueryResult:
        """
        Execute a graph query.
        
        Args:
            query_text: Query text or Cypher query
            query_type: Optional query type hint
            parameters: Query parameters
            
        Returns:
            QueryResult with results
        """
        import time
        start_time = time.time()
        
        # Determine query type if not specified
        if query_type is None:
            query_type = self._detect_query_type(query_text)
        
        # Execute based on type
        if query_type == QueryType.NODE_LOOKUP:
            results = await self._execute_node_lookup(query_text, parameters)
        elif query_type == QueryType.RELATIONSHIP_QUERY:
            results = await self._execute_relationship_query(query_text, parameters)
        elif query_type == QueryType.PATH_FINDING:
            results = await self._execute_path_query(query_text, parameters)
        elif query_type == QueryType.SUBGRAPH:
            results = await self._execute_subgraph_query(query_text, parameters)
        elif query_type == QueryType.AGGREGATION:
            results = await self._execute_aggregation(query_text, parameters)
        else:
            results = await self._execute_pattern_match(query_text, parameters)
        
        execution_time = (time.time() - start_time) * 1000
        
        return QueryResult(
            query_type=query_type,
            results=results,
            metadata={"parameters": parameters},
            execution_time_ms=execution_time,
        )
    
    def _detect_query_type(self, query_text: str) -> QueryType:
        """Detect the type of query from text."""
        query_lower = query_text.lower()
        
        if any(word in query_lower for word in ["path", "connect", "between", "hop"]):
            return QueryType.PATH_FINDING
        elif any(word in query_lower for word in ["related", "relationship", "link"]):
            return QueryType.RELATIONSHIP_QUERY
        elif any(word in query_lower for word in ["count", "average", "sum", "total"]):
            return QueryType.AGGREGATION
        elif any(word in query_lower for word in ["subgraph", "neighborhood", "cluster"]):
            return QueryType.SUBGRAPH
        else:
            return QueryType.NODE_LOOKUP
    
    async def _execute_node_lookup(
        self,
        query_text: str,
        parameters: Optional[Dict],
    ) -> List[Dict]:
        """Execute node lookup query."""
        if self.neo4j_client:
            # Use Neo4j
            label = parameters.get("label") if parameters else None
            props = parameters.get("properties") if parameters else None
            return await self.neo4j_client.find_nodes(label=label, properties=props)
        else:
            # Use local graph
            results = []
            search_term = query_text.lower()
            
            for node_id, data in self.local_graph.nodes(data=True):
                label = data.get("label", "").lower()
                if search_term in label or search_term in node_id.lower():
                    results.append({"id": node_id, **data})
            
            return results
    
    async def _execute_relationship_query(
        self,
        query_text: str,
        parameters: Optional[Dict],
    ) -> List[Dict]:
        """Execute relationship query."""
        if self.neo4j_client and parameters:
            node_id = parameters.get("node_id")
            if node_id:
                return await self.neo4j_client.get_neighbors(node_id)
        
        # Local graph fallback
        results = []
        if parameters and "node_id" in parameters:
            node_id = parameters["node_id"]
            if node_id in self.local_graph:
                for succ in self.local_graph.successors(node_id):
                    edge_data = self.local_graph.edges[node_id, succ]
                    results.append({
                        "source": node_id,
                        "target": succ,
                        **edge_data,
                    })
        
        return results
    
    async def _execute_path_query(
        self,
        query_text: str,
        parameters: Optional[Dict],
    ) -> List[Dict]:
        """Execute path finding query."""
        source = parameters.get("source") if parameters else None
        target = parameters.get("target") if parameters else None
        max_depth = parameters.get("max_depth", 5) if parameters else 5
        
        if not source or not target:
            return []
        
        if self.neo4j_client:
            path = await self.neo4j_client.find_path(source, target, max_depth)
            return [path] if path else []
        
        # Local graph
        try:
            undirected = self.local_graph.to_undirected()
            path = nx.shortest_path(undirected, source, target)
            return [{"path": path, "length": len(path) - 1}]
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []
    
    async def _execute_subgraph_query(
        self,
        query_text: str,
        parameters: Optional[Dict],
    ) -> List[Dict]:
        """Execute subgraph extraction query."""
        center_node = parameters.get("center_node") if parameters else None
        radius = parameters.get("radius", 2) if parameters else 2
        
        if not center_node or center_node not in self.local_graph:
            return []
        
        # BFS to find nodes within radius
        nodes_in_radius = {center_node}
        frontier = {center_node}
        
        for _ in range(radius):
            next_frontier = set()
            for node in frontier:
                next_frontier.update(self.local_graph.predecessors(node))
                next_frontier.update(self.local_graph.successors(node))
            next_frontier -= nodes_in_radius
            nodes_in_radius.update(next_frontier)
            frontier = next_frontier
        
        # Extract subgraph
        subgraph = self.local_graph.subgraph(nodes_in_radius)
        
        return [{
            "nodes": [{"id": n, **data} for n, data in subgraph.nodes(data=True)],
            "edges": [{"source": s, "target": t, **data} for s, t, data in subgraph.edges(data=True)],
        }]
    
    async def _execute_aggregation(
        self,
        query_text: str,
        parameters: Optional[Dict],
    ) -> List[Dict]:
        """Execute aggregation query."""
        if self.neo4j_client:
            stats = await self.neo4j_client.get_statistics()
            return [stats]
        
        # Local graph statistics
        return [{
            "node_count": self.local_graph.number_of_nodes(),
            "edge_count": self.local_graph.number_of_edges(),
            "density": nx.density(self.local_graph),
        }]
    
    async def _execute_pattern_match(
        self,
        query_text: str,
        parameters: Optional[Dict],
    ) -> List[Dict]:
        """Execute pattern matching query."""
        # Basic pattern matching on local graph
        results = []
        
        if parameters and "pattern" in parameters:
            pattern = parameters["pattern"]
            # Simple triple pattern: (source_type)-[rel_type]->(target_type)
            source_type = pattern.get("source_type")
            rel_type = pattern.get("rel_type")
            target_type = pattern.get("target_type")
            
            for source, target, data in self.local_graph.edges(data=True):
                source_data = self.local_graph.nodes[source]
                target_data = self.local_graph.nodes[target]
                
                match = True
                if source_type and source_data.get("node_type") != source_type:
                    match = False
                if rel_type and data.get("relation_type") != rel_type:
                    match = False
                if target_type and target_data.get("node_type") != target_type:
                    match = False
                
                if match:
                    results.append({
                        "source": {"id": source, **source_data},
                        "relationship": data,
                        "target": {"id": target, **target_data},
                    })
        
        return results
    
    def multi_hop_reasoning(
        self,
        start_node: str,
        question: str,
        max_hops: int = 3,
    ) -> List[Dict]:
        """
        Perform multi-hop reasoning from a starting node.
        
        Args:
            start_node: Starting node ID
            question: Question to answer
            max_hops: Maximum reasoning hops
            
        Returns:
            List of reasoning paths with evidence
        """
        if start_node not in self.local_graph:
            return []
        
        paths = []
        
        # BFS to find all paths up to max_hops
        queue = [(start_node, [start_node], [])]  # (current, path, relations)
        visited = {start_node}
        
        while queue:
            current, path, relations = queue.pop(0)
            
            if len(path) > max_hops + 1:
                continue
            
            # Record path if it has multiple hops
            if len(path) > 1:
                paths.append({
                    "path": path,
                    "relations": relations,
                    "length": len(path) - 1,
                    "nodes": [
                        {"id": n, **self.local_graph.nodes[n]}
                        for n in path
                    ],
                })
            
            # Explore neighbors
            for neighbor in self.local_graph.successors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    edge_data = self.local_graph.edges[current, neighbor]
                    queue.append((
                        neighbor,
                        path + [neighbor],
                        relations + [edge_data.get("relation_type", "RELATED")],
                    ))
        
        return paths
    
    def set_local_graph(self, graph: nx.DiGraph) -> None:
        """Set the local graph for queries."""
        self.local_graph = graph
