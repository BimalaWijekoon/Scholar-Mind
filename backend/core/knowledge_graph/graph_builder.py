"""
Graph Builder - Construct knowledge graphs from extracted entities and relations
"""

from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
import networkx as nx


@dataclass
class GraphNode:
    """Represents a node in the knowledge graph."""
    id: str
    label: str
    node_type: str
    properties: Dict


@dataclass
class GraphEdge:
    """Represents an edge in the knowledge graph."""
    source_id: str
    target_id: str
    relation_type: str
    properties: Dict


class GraphBuilder:
    """
    Builder for constructing knowledge graphs from entities and relations.
    
    Uses NetworkX for in-memory graph operations and can export to Neo4j.
    """
    
    def __init__(self):
        """Initialize the graph builder."""
        self.graph = nx.DiGraph()
        self._node_counter = 0
        self._node_index: Dict[str, str] = {}  # text -> node_id
    
    def add_entity(
        self,
        text: str,
        entity_type: str,
        properties: Optional[Dict] = None,
    ) -> str:
        """
        Add an entity node to the graph.
        
        Args:
            text: Entity text
            entity_type: Entity type
            properties: Additional properties
            
        Returns:
            Node ID
        """
        # Check if entity already exists
        normalized_text = text.lower().strip()
        
        if normalized_text in self._node_index:
            return self._node_index[normalized_text]
        
        # Create new node
        node_id = f"entity_{self._node_counter}"
        self._node_counter += 1
        
        self.graph.add_node(
            node_id,
            label=text,
            node_type=entity_type,
            **(properties or {}),
        )
        
        self._node_index[normalized_text] = node_id
        
        return node_id
    
    def add_relation(
        self,
        source_text: str,
        source_type: str,
        target_text: str,
        target_type: str,
        relation_type: str,
        properties: Optional[Dict] = None,
    ) -> Tuple[str, str]:
        """
        Add a relation edge to the graph.
        
        Args:
            source_text: Source entity text
            source_type: Source entity type
            target_text: Target entity text
            target_type: Target entity type
            relation_type: Type of relation
            properties: Additional properties
            
        Returns:
            Tuple of (source_id, target_id)
        """
        # Ensure nodes exist
        source_id = self.add_entity(source_text, source_type)
        target_id = self.add_entity(target_text, target_type)
        
        # Add edge
        self.graph.add_edge(
            source_id,
            target_id,
            relation_type=relation_type,
            **(properties or {}),
        )
        
        return source_id, target_id
    
    def build_from_extraction(
        self,
        entities: List[Dict],
        relations: List[Dict],
    ) -> nx.DiGraph:
        """
        Build graph from extracted entities and relations.
        
        Args:
            entities: List of entity dicts
            relations: List of relation dicts
            
        Returns:
            NetworkX DiGraph
        """
        # Add entities
        for entity in entities:
            self.add_entity(
                text=entity["text"],
                entity_type=entity.get("entity_type", "ENTITY"),
                properties=entity.get("metadata", {}),
            )
        
        # Add relations
        for relation in relations:
            self.add_relation(
                source_text=relation["source_text"],
                source_type=relation.get("source_type", "ENTITY"),
                target_text=relation["target_text"],
                target_type=relation.get("target_type", "ENTITY"),
                relation_type=relation["relation_type"],
                properties={
                    "confidence": relation.get("confidence", 0.5),
                    "context": relation.get("context", ""),
                },
            )
        
        return self.graph
    
    def merge_graphs(self, other_graph: nx.DiGraph) -> None:
        """
        Merge another graph into this one.
        
        Args:
            other_graph: Graph to merge
        """
        # Add nodes
        for node_id, data in other_graph.nodes(data=True):
            label = data.get("label", node_id)
            normalized = label.lower().strip()
            
            if normalized in self._node_index:
                # Merge properties
                existing_id = self._node_index[normalized]
                self.graph.nodes[existing_id].update(data)
            else:
                # Add new node
                new_id = f"entity_{self._node_counter}"
                self._node_counter += 1
                
                self.graph.add_node(new_id, **data)
                self._node_index[normalized] = new_id
        
        # Add edges
        for source, target, data in other_graph.edges(data=True):
            source_label = other_graph.nodes[source].get("label", source)
            target_label = other_graph.nodes[target].get("label", target)
            
            source_id = self._node_index.get(source_label.lower().strip())
            target_id = self._node_index.get(target_label.lower().strip())
            
            if source_id and target_id:
                self.graph.add_edge(source_id, target_id, **data)
    
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """
        Get a node by ID.
        
        Args:
            node_id: Node ID
            
        Returns:
            GraphNode or None
        """
        if node_id not in self.graph:
            return None
        
        data = self.graph.nodes[node_id]
        return GraphNode(
            id=node_id,
            label=data.get("label", node_id),
            node_type=data.get("node_type", "ENTITY"),
            properties={k: v for k, v in data.items() if k not in ["label", "node_type"]},
        )
    
    def get_neighbors(
        self,
        node_id: str,
        direction: str = "both",
    ) -> List[GraphNode]:
        """
        Get neighboring nodes.
        
        Args:
            node_id: Node ID
            direction: 'in', 'out', or 'both'
            
        Returns:
            List of neighbor GraphNodes
        """
        neighbors = set()
        
        if direction in ("in", "both"):
            neighbors.update(self.graph.predecessors(node_id))
        
        if direction in ("out", "both"):
            neighbors.update(self.graph.successors(node_id))
        
        return [self.get_node(nid) for nid in neighbors if nid]
    
    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_length: int = 5,
    ) -> Optional[List[str]]:
        """
        Find shortest path between two nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            max_length: Maximum path length
            
        Returns:
            List of node IDs in path, or None
        """
        try:
            path = nx.shortest_path(
                self.graph.to_undirected(),
                source_id,
                target_id,
            )
            
            if len(path) <= max_length + 1:
                return path
        except nx.NetworkXNoPath:
            pass
        
        return None
    
    def get_subgraph(
        self,
        node_ids: List[str],
        include_neighbors: bool = True,
    ) -> nx.DiGraph:
        """
        Get a subgraph containing specified nodes.
        
        Args:
            node_ids: Node IDs to include
            include_neighbors: Whether to include immediate neighbors
            
        Returns:
            Subgraph as DiGraph
        """
        nodes_to_include = set(node_ids)
        
        if include_neighbors:
            for node_id in node_ids:
                if node_id in self.graph:
                    nodes_to_include.update(self.graph.predecessors(node_id))
                    nodes_to_include.update(self.graph.successors(node_id))
        
        return self.graph.subgraph(nodes_to_include).copy()
    
    def get_statistics(self) -> Dict:
        """Get graph statistics."""
        return {
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
            "is_connected": nx.is_weakly_connected(self.graph) if self.graph.number_of_nodes() > 0 else False,
            "num_components": nx.number_weakly_connected_components(self.graph),
        }
    
    def export_to_dict(self) -> Dict:
        """Export graph to dictionary format."""
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                **data,
            })
        
        edges = []
        for source, target, data in self.graph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                **data,
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "statistics": self.get_statistics(),
        }
    
    def clear(self) -> None:
        """Clear the graph."""
        self.graph.clear()
        self._node_counter = 0
        self._node_index.clear()
