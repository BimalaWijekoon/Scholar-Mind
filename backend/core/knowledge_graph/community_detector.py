"""
Community Detector - Detect communities and clusters in knowledge graphs
"""

from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
import networkx as nx
from collections import defaultdict


@dataclass
class Community:
    """Represents a detected community."""
    id: int
    nodes: List[str]
    size: int
    density: float
    central_nodes: List[str]
    label: Optional[str]


class CommunityDetector:
    """
    Detect communities in knowledge graphs.
    
    Supports:
    - Louvain algorithm
    - Label propagation
    - Girvan-Newman
    - K-core decomposition
    """
    
    def __init__(self, algorithm: str = "louvain"):
        """
        Initialize the community detector.
        
        Args:
            algorithm: Community detection algorithm to use
        """
        self.algorithm = algorithm
    
    def detect(self, graph: nx.Graph, resolution: float = 1.0) -> List[Community]:
        """
        Detect communities in a graph.
        
        Args:
            graph: NetworkX graph
            resolution: Resolution parameter for community detection
            
        Returns:
            List of Community objects
        """
        if graph.number_of_nodes() == 0:
            return []
        
        # Convert to undirected for community detection
        if graph.is_directed():
            undirected = graph.to_undirected()
        else:
            undirected = graph
        
        # Detect communities based on algorithm
        if self.algorithm == "louvain":
            communities = self._detect_louvain(undirected, resolution)
        elif self.algorithm == "label_propagation":
            communities = self._detect_label_propagation(undirected)
        elif self.algorithm == "girvan_newman":
            communities = self._detect_girvan_newman(undirected)
        else:
            communities = self._detect_louvain(undirected, resolution)
        
        # Build Community objects
        result = []
        for i, node_set in enumerate(communities):
            nodes = list(node_set)
            subgraph = undirected.subgraph(nodes)
            
            # Calculate density
            density = nx.density(subgraph) if len(nodes) > 1 else 0.0
            
            # Find central nodes (by degree)
            degrees = dict(subgraph.degree())
            sorted_nodes = sorted(degrees.keys(), key=lambda x: degrees[x], reverse=True)
            central_nodes = sorted_nodes[:min(3, len(sorted_nodes))]
            
            # Generate label from central node labels
            label = self._generate_community_label(graph, central_nodes)
            
            result.append(Community(
                id=i,
                nodes=nodes,
                size=len(nodes),
                density=density,
                central_nodes=central_nodes,
                label=label,
            ))
        
        # Sort by size
        result.sort(key=lambda c: c.size, reverse=True)
        
        return result
    
    def _detect_louvain(self, graph: nx.Graph, resolution: float) -> List[Set[str]]:
        """Detect communities using Louvain algorithm."""
        try:
            from networkx.algorithms.community import louvain_communities
            communities = louvain_communities(graph, resolution=resolution)
            return list(communities)
        except ImportError:
            # Fallback to greedy modularity
            from networkx.algorithms.community import greedy_modularity_communities
            return list(greedy_modularity_communities(graph))
    
    def _detect_label_propagation(self, graph: nx.Graph) -> List[Set[str]]:
        """Detect communities using label propagation."""
        from networkx.algorithms.community import label_propagation_communities
        return list(label_propagation_communities(graph))
    
    def _detect_girvan_newman(self, graph: nx.Graph, k: int = 5) -> List[Set[str]]:
        """Detect communities using Girvan-Newman algorithm."""
        from networkx.algorithms.community import girvan_newman
        
        comp = girvan_newman(graph)
        
        # Get first k levels of hierarchy
        for _ in range(min(k, graph.number_of_nodes() - 1)):
            communities = next(comp, None)
            if communities is None:
                break
            if len(communities) >= k:
                break
        
        return list(communities) if communities else [set(graph.nodes())]
    
    def _generate_community_label(
        self,
        graph: nx.Graph,
        central_nodes: List[str],
    ) -> str:
        """Generate a label for a community based on its central nodes."""
        labels = []
        
        for node_id in central_nodes[:2]:
            if node_id in graph.nodes:
                node_data = graph.nodes[node_id]
                label = node_data.get("label", node_id)
                labels.append(label)
        
        if labels:
            return " & ".join(labels)
        return "Community"
    
    def get_node_community(
        self,
        graph: nx.Graph,
        node_id: str,
    ) -> Optional[Community]:
        """
        Get the community a node belongs to.
        
        Args:
            graph: NetworkX graph
            node_id: Node ID
            
        Returns:
            Community containing the node, or None
        """
        if node_id not in graph:
            return None
        
        communities = self.detect(graph)
        
        for community in communities:
            if node_id in community.nodes:
                return community
        
        return None
    
    def find_bridge_nodes(self, graph: nx.Graph) -> List[str]:
        """
        Find nodes that bridge multiple communities.
        
        Args:
            graph: NetworkX graph
            
        Returns:
            List of bridge node IDs
        """
        if graph.is_directed():
            undirected = graph.to_undirected()
        else:
            undirected = graph
        
        # Detect communities
        communities = self.detect(graph)
        
        # Map nodes to communities
        node_to_community = {}
        for i, community in enumerate(communities):
            for node in community.nodes:
                node_to_community[node] = i
        
        # Find nodes with neighbors in different communities
        bridge_nodes = []
        
        for node in undirected.nodes():
            node_comm = node_to_community.get(node)
            if node_comm is None:
                continue
            
            neighbor_communities = set()
            for neighbor in undirected.neighbors(node):
                neighbor_comm = node_to_community.get(neighbor)
                if neighbor_comm is not None:
                    neighbor_communities.add(neighbor_comm)
            
            # Node is a bridge if it connects to multiple communities
            if len(neighbor_communities) > 1:
                bridge_nodes.append(node)
        
        return bridge_nodes
    
    def compute_community_graph(
        self,
        graph: nx.Graph,
    ) -> Tuple[nx.Graph, List[Community]]:
        """
        Create a graph where nodes are communities.
        
        Args:
            graph: Original graph
            
        Returns:
            Tuple of (community graph, list of communities)
        """
        communities = self.detect(graph)
        
        # Map nodes to community IDs
        node_to_community = {}
        for community in communities:
            for node in community.nodes:
                node_to_community[node] = community.id
        
        # Create community graph
        comm_graph = nx.Graph()
        
        # Add community nodes
        for community in communities:
            comm_graph.add_node(
                community.id,
                size=community.size,
                label=community.label,
            )
        
        # Add edges between communities
        edge_weights = defaultdict(int)
        
        for source, target in graph.edges():
            source_comm = node_to_community.get(source)
            target_comm = node_to_community.get(target)
            
            if source_comm is not None and target_comm is not None:
                if source_comm != target_comm:
                    edge_key = tuple(sorted([source_comm, target_comm]))
                    edge_weights[edge_key] += 1
        
        for (comm1, comm2), weight in edge_weights.items():
            comm_graph.add_edge(comm1, comm2, weight=weight)
        
        return comm_graph, communities
    
    def get_community_statistics(
        self,
        graph: nx.Graph,
    ) -> Dict:
        """
        Get statistics about communities in the graph.
        
        Args:
            graph: NetworkX graph
            
        Returns:
            Dictionary with community statistics
        """
        communities = self.detect(graph)
        
        if not communities:
            return {
                "num_communities": 0,
                "modularity": 0.0,
                "avg_size": 0,
                "max_size": 0,
                "min_size": 0,
            }
        
        sizes = [c.size for c in communities]
        
        # Calculate modularity
        if graph.is_directed():
            undirected = graph.to_undirected()
        else:
            undirected = graph
        
        try:
            community_sets = [set(c.nodes) for c in communities]
            modularity = nx.algorithms.community.modularity(undirected, community_sets)
        except Exception:
            modularity = 0.0
        
        return {
            "num_communities": len(communities),
            "modularity": modularity,
            "avg_size": sum(sizes) / len(sizes),
            "max_size": max(sizes),
            "min_size": min(sizes),
            "sizes": sizes,
        }
