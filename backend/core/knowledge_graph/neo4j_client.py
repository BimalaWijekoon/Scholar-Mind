"""
Neo4j Client - Interface for Neo4j graph database operations
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from contextlib import asynccontextmanager
from neo4j import AsyncGraphDatabase, GraphDatabase
import logging


logger = logging.getLogger(__name__)


@dataclass
class Neo4jConfig:
    """Neo4j connection configuration."""
    uri: str
    username: str
    password: str
    database: str = "neo4j"


class Neo4jClient:
    """
    Async client for Neo4j graph database.
    
    Provides:
    - Connection management
    - CRUD operations for nodes and relationships
    - Cypher query execution
    """
    
    def __init__(
        self,
        uri: str = None,
        user: str = None,
        password: str = None,
        database: str = "neo4j",
        config: Neo4jConfig = None,
    ):
        """
        Initialize the Neo4j client.
        
        Args:
            uri: Neo4j connection URI (bolt://...)
            user: Username
            password: Password
            database: Database name (default: "neo4j")
            config: Alternative: pass a Neo4jConfig dataclass
        """
        if config is not None:
            self.config = config
        elif uri and user and password:
            self.config = Neo4jConfig(
                uri=uri,
                username=user,
                password=password,
                database=database,
            )
        else:
            raise ValueError(
                "Neo4jClient requires either (uri, user, password) kwargs "
                "or a Neo4jConfig instance via config="
            )
        self._driver = None
        self._async_driver = None
    
    async def connect(self) -> None:
        """Establish async connection to Neo4j."""
        self._async_driver = AsyncGraphDatabase.driver(
            self.config.uri,
            auth=(self.config.username, self.config.password),
        )
        
        # Verify connectivity
        async with self._async_driver.session(database=self.config.database) as session:
            await session.run("RETURN 1")
        
        logger.info(f"Connected to Neo4j at {self.config.uri}")
    
    def connect_sync(self) -> None:
        """Establish sync connection to Neo4j."""
        self._driver = GraphDatabase.driver(
            self.config.uri,
            auth=(self.config.username, self.config.password),
        )
        
        # Verify connectivity
        with self._driver.session(database=self.config.database) as session:
            session.run("RETURN 1")
        
        logger.info(f"Connected to Neo4j at {self.config.uri}")
    
    async def close(self) -> None:
        """Close the connection."""
        if self._async_driver:
            await self._async_driver.close()
        if self._driver:
            self._driver.close()
    
    @asynccontextmanager
    async def session(self):
        """Get an async session."""
        session = self._async_driver.session(database=self.config.database)
        try:
            yield session
        finally:
            await session.close()
    
    async def create_node(
        self,
        label: str,
        properties: Dict[str, Any],
    ) -> str:
        """
        Create a node in the graph.
        
        Args:
            label: Node label
            properties: Node properties
            
        Returns:
            Node ID
        """
        query = f"""
        CREATE (n:{label} $properties)
        RETURN elementId(n) as id
        """
        
        async with self.session() as session:
            result = await session.run(query, properties=properties)
            record = await result.single()
            return record["id"]
    
    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a relationship between two nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            rel_type: Relationship type
            properties: Relationship properties
            
        Returns:
            Relationship ID
        """
        query = f"""
        MATCH (a), (b)
        WHERE elementId(a) = $source_id AND elementId(b) = $target_id
        CREATE (a)-[r:{rel_type} $properties]->(b)
        RETURN elementId(r) as id
        """
        
        async with self.session() as session:
            result = await session.run(
                query,
                source_id=source_id,
                target_id=target_id,
                properties=properties or {},
            )
            record = await result.single()
            return record["id"]
    
    async def get_node(self, node_id: str) -> Optional[Dict]:
        """
        Get a node by ID.
        
        Args:
            node_id: Node ID
            
        Returns:
            Node data or None
        """
        query = """
        MATCH (n)
        WHERE elementId(n) = $node_id
        RETURN n, labels(n) as labels
        """
        
        async with self.session() as session:
            result = await session.run(query, node_id=node_id)
            record = await result.single()
            
            if record:
                node = dict(record["n"])
                node["id"] = node_id
                node["labels"] = record["labels"]
                return node
        
        return None
    
    async def find_nodes(
        self,
        label: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """
        Find nodes matching criteria.
        
        Args:
            label: Optional node label
            properties: Optional property filters
            limit: Maximum results
            
        Returns:
            List of matching nodes
        """
        if label:
            match_clause = f"MATCH (n:{label})"
        else:
            match_clause = "MATCH (n)"
        
        where_clauses = []
        params = {"limit": limit}
        
        if properties:
            for i, (key, value) in enumerate(properties.items()):
                where_clauses.append(f"n.{key} = $prop_{i}")
                params[f"prop_{i}"] = value
        
        where_clause = ""
        if where_clauses:
            where_clause = "WHERE " + " AND ".join(where_clauses)
        
        query = f"""
        {match_clause}
        {where_clause}
        RETURN n, labels(n) as labels, elementId(n) as id
        LIMIT $limit
        """
        
        async with self.session() as session:
            result = await session.run(query, **params)
            records = await result.data()
            
            nodes = []
            for record in records:
                node = dict(record["n"])
                node["id"] = record["id"]
                node["labels"] = record["labels"]
                nodes.append(node)
            
            return nodes
    
    async def get_neighbors(
        self,
        node_id: str,
        direction: str = "both",
        rel_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """
        Get neighbors of a node.
        
        Args:
            node_id: Node ID
            direction: 'in', 'out', or 'both'
            rel_type: Optional relationship type filter
            limit: Maximum results
            
        Returns:
            List of neighbor nodes with relationship info
        """
        if direction == "in":
            pattern = "<-[r{rel_filter}]-(m)"
        elif direction == "out":
            pattern = "-[r{rel_filter}]->(m)"
        else:
            pattern = "-[r{rel_filter}]-(m)"
        
        rel_filter = f":{rel_type}" if rel_type else ""
        pattern = pattern.format(rel_filter=rel_filter)
        
        query = f"""
        MATCH (n){pattern}
        WHERE elementId(n) = $node_id
        RETURN m, labels(m) as labels, elementId(m) as id,
               type(r) as rel_type, properties(r) as rel_props
        LIMIT $limit
        """
        
        async with self.session() as session:
            result = await session.run(query, node_id=node_id, limit=limit)
            records = await result.data()
            
            neighbors = []
            for record in records:
                neighbor = dict(record["m"])
                neighbor["id"] = record["id"]
                neighbor["labels"] = record["labels"]
                neighbor["relationship"] = {
                    "type": record["rel_type"],
                    "properties": record["rel_props"],
                }
                neighbors.append(neighbor)
            
            return neighbors
    
    async def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5,
    ) -> Optional[List[Dict]]:
        """
        Find shortest path between two nodes.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            max_depth: Maximum path length
            
        Returns:
            Path as list of nodes and relationships
        """
        query = f"""
        MATCH p = shortestPath((a)-[*1..{max_depth}]-(b))
        WHERE elementId(a) = $source_id AND elementId(b) = $target_id
        RETURN [node in nodes(p) | {{
            id: elementId(node),
            labels: labels(node),
            properties: properties(node)
        }}] as nodes,
        [rel in relationships(p) | {{
            type: type(rel),
            properties: properties(rel)
        }}] as relationships
        """
        
        async with self.session() as session:
            result = await session.run(
                query,
                source_id=source_id,
                target_id=target_id,
            )
            record = await result.single()
            
            if record:
                return {
                    "nodes": record["nodes"],
                    "relationships": record["relationships"],
                }
        
        return None
    
    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict]:
        """
        Execute a Cypher query.
        
        Args:
            query: Cypher query
            parameters: Query parameters
            
        Returns:
            Query results
        """
        async with self.session() as session:
            result = await session.run(query, **(parameters or {}))
            return await result.data()
    
    async def import_graph(
        self,
        nodes: List[Dict],
        relationships: List[Dict],
    ) -> Dict[str, int]:
        """
        Import a graph (batch operation).
        
        Args:
            nodes: List of node dicts with 'label' and 'properties'
            relationships: List of relationship dicts
            
        Returns:
            Statistics about imported entities
        """
        nodes_created = 0
        rels_created = 0
        
        # Create nodes
        for node in nodes:
            await self.create_node(node["label"], node.get("properties", {}))
            nodes_created += 1
        
        # Create relationships
        for rel in relationships:
            await self.create_relationship(
                rel["source_id"],
                rel["target_id"],
                rel["type"],
                rel.get("properties"),
            )
            rels_created += 1
        
        return {
            "nodes_created": nodes_created,
            "relationships_created": rels_created,
        }
    
    async def get_statistics(self) -> Dict:
        """Get database statistics."""
        query = """
        MATCH (n)
        WITH count(n) as node_count
        MATCH ()-[r]->()
        WITH node_count, count(r) as rel_count
        RETURN node_count, rel_count
        """
        
        async with self.session() as session:
            result = await session.run(query)
            record = await result.single()
            
            return {
                "node_count": record["node_count"] if record else 0,
                "relationship_count": record["rel_count"] if record else 0,
            }
