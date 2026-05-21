"""
Graph Tool - Knowledge graph query tool for agents
"""

from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass


@dataclass
class GraphQueryResult:
    """Result from graph query."""
    entities: List[Dict]
    relations: List[Dict]
    paths: List[List[str]]
    metadata: Dict


class GraphTool:
    """
    Knowledge graph query tool for agents.
    
    Provides:
    - Entity lookup
    - Relationship queries
    - Path finding
    - Subgraph extraction
    """
    
    name = "graph_query"
    description = """Query the knowledge graph for entities, relationships, and connections.
    
    Use this tool to:
    - Find entities and their properties
    - Discover relationships between concepts
    - Find paths connecting different entities
    - Explore neighborhoods in the knowledge graph
    
    Input: A query describing what to find in the graph
    Output: Entities, relationships, and paths matching the query"""
    
    def __init__(
        self,
        graph_query_engine: Optional[Any] = None,
        neo4j_client: Optional[Any] = None,
    ):
        """
        Initialize the graph tool.
        
        Args:
            graph_query_engine: Graph query engine instance
            neo4j_client: Neo4j client for direct queries
        """
        self.graph_query_engine = graph_query_engine
        self.neo4j_client = neo4j_client
    
    def run(self, query: str, **kwargs) -> GraphQueryResult:
        """
        Execute a graph query.
        
        Args:
            query: Graph query
            **kwargs: Additional parameters
            
        Returns:
            Graph query results
        """
        operation = kwargs.get("operation", "search")
        
        if operation == "find_entity":
            return self._find_entity(kwargs.get("entity_name", query))
        elif operation == "find_relations":
            return self._find_relations(
                kwargs.get("entity_id"),
                kwargs.get("relation_type"),
            )
        elif operation == "find_path":
            return self._find_path(
                kwargs.get("source"),
                kwargs.get("target"),
                kwargs.get("max_depth", 5),
            )
        elif operation == "get_neighbors":
            return self._get_neighbors(
                kwargs.get("entity_id"),
                kwargs.get("depth", 1),
            )
        else:
            return self._general_search(query)
    
    def _find_entity(self, entity_name: str) -> GraphQueryResult:
        """Find an entity by name."""
        entities = []
        
        if self.neo4j_client:
            import asyncio
            try:
                results = asyncio.run(
                    self.neo4j_client.find_nodes(
                        properties={"label": entity_name},
                        limit=10,
                    )
                )
                entities = results
            except Exception:
                pass
        
        return GraphQueryResult(
            entities=entities,
            relations=[],
            paths=[],
            metadata={"operation": "find_entity", "query": entity_name},
        )
    
    def _find_relations(
        self,
        entity_id: Optional[str],
        relation_type: Optional[str],
    ) -> GraphQueryResult:
        """Find relations for an entity."""
        relations = []
        
        if self.neo4j_client and entity_id:
            import asyncio
            try:
                neighbors = asyncio.run(
                    self.neo4j_client.get_neighbors(
                        node_id=entity_id,
                        rel_type=relation_type,
                        limit=20,
                    )
                )
                
                for neighbor in neighbors:
                    rel = neighbor.get("relationship", {})
                    relations.append({
                        "source": entity_id,
                        "target": neighbor.get("id"),
                        "type": rel.get("type"),
                        "properties": rel.get("properties", {}),
                    })
            except Exception:
                pass
        
        return GraphQueryResult(
            entities=[],
            relations=relations,
            paths=[],
            metadata={"operation": "find_relations", "entity_id": entity_id},
        )
    
    def _find_path(
        self,
        source: Optional[str],
        target: Optional[str],
        max_depth: int,
    ) -> GraphQueryResult:
        """Find path between entities."""
        paths = []
        
        if self.neo4j_client and source and target:
            import asyncio
            try:
                path_result = asyncio.run(
                    self.neo4j_client.find_path(
                        source_id=source,
                        target_id=target,
                        max_depth=max_depth,
                    )
                )
                
                if path_result:
                    paths = [[n["id"] for n in path_result.get("nodes", [])]]
            except Exception:
                pass
        
        return GraphQueryResult(
            entities=[],
            relations=[],
            paths=paths,
            metadata={"operation": "find_path", "source": source, "target": target},
        )
    
    def _get_neighbors(self, entity_id: Optional[str], depth: int) -> GraphQueryResult:
        """Get neighborhood of an entity."""
        entities = []
        relations = []
        
        if self.neo4j_client and entity_id:
            import asyncio
            try:
                neighbors = asyncio.run(
                    self.neo4j_client.get_neighbors(
                        node_id=entity_id,
                        limit=50,
                    )
                )
                
                for neighbor in neighbors:
                    entities.append({
                        "id": neighbor.get("id"),
                        "label": neighbor.get("label"),
                        "labels": neighbor.get("labels", []),
                    })
                    
                    rel = neighbor.get("relationship", {})
                    relations.append({
                        "source": entity_id,
                        "target": neighbor.get("id"),
                        "type": rel.get("type"),
                    })
            except Exception:
                pass
        
        return GraphQueryResult(
            entities=entities,
            relations=relations,
            paths=[],
            metadata={"operation": "get_neighbors", "entity_id": entity_id},
        )
    
    def _general_search(self, query: str) -> GraphQueryResult:
        """Perform general graph search."""
        if self.graph_query_engine:
            import asyncio
            try:
                result = asyncio.run(
                    self.graph_query_engine.query(query)
                )
                
                return GraphQueryResult(
                    entities=result.results,
                    relations=[],
                    paths=[],
                    metadata={"operation": "search", "query": query},
                )
            except Exception:
                pass
        
        return GraphQueryResult(
            entities=[],
            relations=[],
            paths=[],
            metadata={"operation": "search", "query": query, "error": "No results"},
        )
    
    async def arun(self, query: str, **kwargs) -> GraphQueryResult:
        """Async version of run."""
        return self.run(query, **kwargs)
    
    def format_results(self, results: GraphQueryResult) -> str:
        """Format results for LLM consumption."""
        parts = []
        
        if results.entities:
            parts.append("Entities found:")
            for entity in results.entities[:10]:
                label = entity.get("label", entity.get("id", "Unknown"))
                parts.append(f"  - {label}")
        
        if results.relations:
            parts.append("\nRelationships:")
            for rel in results.relations[:10]:
                rel_type = rel.get("type", "RELATED")
                parts.append(f"  - ({rel['source']}) -[{rel_type}]-> ({rel['target']})")
        
        if results.paths:
            parts.append("\nPaths:")
            for path in results.paths[:5]:
                parts.append(f"  - {' -> '.join(path)}")
        
        if not parts:
            return "No graph results found."
        
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
                        "description": "The graph query or entity name to search for",
                    },
                    "operation": {
                        "type": "string",
                        "enum": ["search", "find_entity", "find_relations", "find_path", "get_neighbors"],
                        "description": "Type of graph operation",
                        "default": "search",
                    },
                    "entity_id": {
                        "type": "string",
                        "description": "Entity ID for relationship/neighbor queries",
                    },
                    "source": {
                        "type": "string",
                        "description": "Source entity ID for path finding",
                    },
                    "target": {
                        "type": "string",
                        "description": "Target entity ID for path finding",
                    },
                },
                "required": ["query"],
            },
        }
