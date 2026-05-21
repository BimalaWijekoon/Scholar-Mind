"""
Unit Tests for Knowledge Graph Components
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import networkx as nx


class TestGraphBuilder:
    """Tests for graph building functionality."""
    
    def test_graph_builder_initialization(self):
        """Test GraphBuilder can be initialized."""
        from backend.core.knowledge_graph import GraphBuilder
        
        builder = GraphBuilder()
        assert builder is not None
        assert isinstance(builder.graph, nx.Graph)
    
    def test_add_node(self):
        """Test adding a node to the graph."""
        from backend.core.knowledge_graph import GraphBuilder
        
        builder = GraphBuilder()
        
        node_id = builder.add_node(
            node_id="entity-1",
            label="Machine Learning",
            node_type="CONCEPT",
            properties={"confidence": 0.95},
        )
        
        assert node_id is not None
        assert "entity-1" in builder.graph.nodes
        assert builder.graph.nodes["entity-1"]["label"] == "Machine Learning"
    
    def test_add_edge(self):
        """Test adding an edge to the graph."""
        from backend.core.knowledge_graph import GraphBuilder
        
        builder = GraphBuilder()
        
        builder.add_node("node-1", "Node 1", "CONCEPT")
        builder.add_node("node-2", "Node 2", "CONCEPT")
        
        builder.add_edge(
            source_id="node-1",
            target_id="node-2",
            relation_type="RELATED_TO",
            properties={"weight": 0.8},
        )
        
        assert builder.graph.has_edge("node-1", "node-2")
    
    def test_build_from_extraction(self, sample_entities, sample_relations):
        """Test building graph from extracted data."""
        from backend.core.knowledge_graph import GraphBuilder
        
        builder = GraphBuilder()
        builder.build_from_extraction(sample_entities, sample_relations)
        
        assert builder.graph.number_of_nodes() > 0
    
    def test_get_node(self):
        """Test getting a node by ID."""
        from backend.core.knowledge_graph import GraphBuilder
        
        builder = GraphBuilder()
        builder.add_node("test-node", "Test Node", "CONCEPT")
        
        node = builder.get_node("test-node")
        
        assert node is not None
        assert node.label == "Test Node"
    
    def test_get_nonexistent_node(self):
        """Test getting a non-existent node."""
        from backend.core.knowledge_graph import GraphBuilder
        
        builder = GraphBuilder()
        
        node = builder.get_node("nonexistent")
        
        assert node is None
    
    def test_get_neighbors(self):
        """Test getting neighbors of a node."""
        from backend.core.knowledge_graph import GraphBuilder
        
        builder = GraphBuilder()
        
        builder.add_node("center", "Center", "CONCEPT")
        builder.add_node("neighbor-1", "Neighbor 1", "CONCEPT")
        builder.add_node("neighbor-2", "Neighbor 2", "CONCEPT")
        
        builder.add_edge("center", "neighbor-1", "RELATED")
        builder.add_edge("center", "neighbor-2", "RELATED")
        
        neighbors = builder.get_neighbors("center")
        
        assert len(neighbors) == 2
    
    def test_find_path(self):
        """Test finding path between nodes."""
        from backend.core.knowledge_graph import GraphBuilder
        
        builder = GraphBuilder()
        
        # Create a chain: A -> B -> C -> D
        for i, label in enumerate(["A", "B", "C", "D"]):
            builder.add_node(label, label, "CONCEPT")
        
        builder.add_edge("A", "B", "NEXT")
        builder.add_edge("B", "C", "NEXT")
        builder.add_edge("C", "D", "NEXT")
        
        path = builder.find_path("A", "D")
        
        assert path is not None
        assert len(path) == 4
        assert path[0] == "A"
        assert path[-1] == "D"
    
    def test_get_statistics(self):
        """Test getting graph statistics."""
        from backend.core.knowledge_graph import GraphBuilder
        
        builder = GraphBuilder()
        
        builder.add_node("node-1", "Node 1", "CONCEPT")
        builder.add_node("node-2", "Node 2", "CONCEPT")
        builder.add_edge("node-1", "node-2", "RELATED")
        
        stats = builder.get_statistics()
        
        assert stats["node_count"] == 2
        assert stats["edge_count"] == 1


class TestNeo4jClient:
    """Tests for Neo4j client."""
    
    @pytest.mark.asyncio
    async def test_neo4j_client_initialization(self):
        """Test Neo4jClient can be initialized."""
        with patch("neo4j.AsyncGraphDatabase") as mock_driver:
            from backend.core.knowledge_graph import Neo4jClient
            
            client = Neo4jClient(
                uri="bolt://localhost:7687",
                user="neo4j",
                password="password",
            )
            
            assert client is not None
    
    @pytest.mark.asyncio
    async def test_create_node(self, mock_neo4j_client):
        """Test creating a node in Neo4j."""
        node_id = await mock_neo4j_client.create_node(
            label="CONCEPT",
            properties={"text": "Machine Learning"},
        )
        
        assert node_id is not None
    
    @pytest.mark.asyncio
    async def test_create_relationship(self, mock_neo4j_client):
        """Test creating a relationship in Neo4j."""
        result = await mock_neo4j_client.create_relationship(
            source_id="node-1",
            target_id="node-2",
            rel_type="RELATED_TO",
            properties={"weight": 0.9},
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_node(self, mock_neo4j_client):
        """Test getting a node from Neo4j."""
        node = await mock_neo4j_client.get_node("node-1")
        
        assert node is not None
        assert "id" in node
    
    @pytest.mark.asyncio
    async def test_get_neighbors(self, mock_neo4j_client):
        """Test getting neighbors from Neo4j."""
        neighbors = await mock_neo4j_client.get_neighbors("node-1")
        
        assert isinstance(neighbors, list)
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, mock_neo4j_client):
        """Test getting statistics from Neo4j."""
        stats = await mock_neo4j_client.get_statistics()
        
        assert "node_count" in stats
        assert "relationship_count" in stats


class TestCommunityDetector:
    """Tests for community detection."""
    
    def test_community_detector_initialization(self):
        """Test CommunityDetector can be initialized."""
        from backend.core.knowledge_graph import CommunityDetector
        
        detector = CommunityDetector()
        assert detector is not None
    
    def test_detect_communities_louvain(self):
        """Test Louvain community detection."""
        from backend.core.knowledge_graph import CommunityDetector
        
        detector = CommunityDetector(algorithm="louvain")
        
        # Create a graph with clear communities
        graph = nx.Graph()
        
        # Community 1
        for i in range(5):
            graph.add_node(f"c1-{i}", label=f"Node C1-{i}")
        for i in range(4):
            graph.add_edge(f"c1-{i}", f"c1-{i+1}")
        graph.add_edge("c1-0", "c1-4")
        
        # Community 2
        for i in range(5):
            graph.add_node(f"c2-{i}", label=f"Node C2-{i}")
        for i in range(4):
            graph.add_edge(f"c2-{i}", f"c2-{i+1}")
        graph.add_edge("c2-0", "c2-4")
        
        # Weak connection between communities
        graph.add_edge("c1-0", "c2-0")
        
        communities = detector.detect(graph)
        
        assert len(communities) >= 1
    
    def test_detect_communities_label_propagation(self):
        """Test label propagation community detection."""
        from backend.core.knowledge_graph import CommunityDetector
        
        detector = CommunityDetector(algorithm="label_propagation")
        
        graph = nx.Graph()
        graph.add_edges_from([("a", "b"), ("b", "c"), ("c", "a")])
        
        communities = detector.detect(graph)
        
        assert len(communities) >= 1
    
    def test_empty_graph(self):
        """Test detection on empty graph."""
        from backend.core.knowledge_graph import CommunityDetector
        
        detector = CommunityDetector()
        
        graph = nx.Graph()
        
        communities = detector.detect(graph)
        
        assert len(communities) == 0


class TestGraphQueryEngine:
    """Tests for graph query engine."""
    
    def test_query_engine_initialization(self, mock_neo4j_client):
        """Test GraphQueryEngine can be initialized."""
        from backend.core.knowledge_graph import GraphQueryEngine
        
        engine = GraphQueryEngine(neo4j_client=mock_neo4j_client)
        assert engine is not None
    
    @pytest.mark.asyncio
    async def test_natural_language_query(self, mock_neo4j_client):
        """Test natural language query."""
        from backend.core.knowledge_graph import GraphQueryEngine
        
        engine = GraphQueryEngine(neo4j_client=mock_neo4j_client)
        
        # Mock LLM response
        with patch.object(engine, "_convert_to_cypher") as mock_convert:
            mock_convert.return_value = "MATCH (n) RETURN n LIMIT 10"
            
            result = await engine.query("Find all concepts related to machine learning")
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_cypher_query(self, mock_neo4j_client):
        """Test executing a Cypher query."""
        from backend.core.knowledge_graph import GraphQueryEngine
        
        engine = GraphQueryEngine(neo4j_client=mock_neo4j_client)
        
        mock_neo4j_client.execute_query.return_value = [{"n": {"text": "Test"}}]
        
        result = await engine.execute_cypher("MATCH (n) RETURN n LIMIT 10")
        
        assert result is not None
