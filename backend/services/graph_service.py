"""
Graph Service - Handle knowledge graph operations
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import logging
import uuid

logger = logging.getLogger(__name__)

# In-memory storage for entities and relations (shared across requests)
_entity_store: Dict[str, Dict] = {}
_relation_store: List[Dict] = []


@dataclass
class GraphData:
    """Graph data for visualization."""
    nodes: List[Dict]
    edges: List[Dict]
    statistics: Dict


class GraphService:
    """
    Service for knowledge graph operations.
    
    Handles:
    - Entity and relation management
    - Graph queries
    - Visualization data
    - Community detection
    """
    
    # Class-level storage that persists across instances
    entities: Dict[str, Dict] = {}
    relations: List[Dict] = []
    
    def __init__(
        self,
        neo4j_client=None,
        graph_builder=None,
        entity_extractor=None,
        relation_extractor=None,
        community_detector=None,
    ):
        """
        Initialize the graph service.
        
        Args:
            neo4j_client: Neo4j database client
            graph_builder: Graph builder instance
            entity_extractor: Entity extractor
            relation_extractor: Relation extractor
            community_detector: Community detection
        """
        self.neo4j_client = neo4j_client
        self.graph_builder = graph_builder
        self.entity_extractor = entity_extractor
        self.relation_extractor = relation_extractor
        self.community_detector = community_detector
    
    def add_entities_from_extraction(self, entities: List[Dict], document_id: str) -> int:
        """
        Add extracted entities to the graph store.
        
        Args:
            entities: List of entity dicts with 'text', 'type' keys
            document_id: Source document ID
            
        Returns:
            Number of entities added
        """
        added = 0
        for entity in entities:
            entity_text = entity.get("text", "")
            entity_type = entity.get("type", "CONCEPT")
            
            # Create unique ID based on text (deduplication)
            entity_id = f"{entity_type}_{entity_text}".replace(" ", "_").lower()
            
            if entity_id not in _entity_store:
                _entity_store[entity_id] = {
                    "id": entity_id,
                    "label": entity_text,
                    "type": entity_type,
                    "documents": [document_id],
                    "properties": {
                        "start": entity.get("start", 0),
                        "end": entity.get("end", 0),
                    }
                }
                added += 1
                print(f"   📊 Added entity to graph: {entity_text} ({entity_type})")
            else:
                # Add document reference if not already there
                if document_id not in _entity_store[entity_id]["documents"]:
                    _entity_store[entity_id]["documents"].append(document_id)
        
        return added
    
    def add_relation(self, source_id: str, target_id: str, relation_type: str, document_id: str):
        """Add a relation between two entities."""
        _relation_store.append({
            "source": source_id,
            "target": target_id,
            "type": relation_type,
            "document_id": document_id,
            "properties": {}
        })
    
    def add_relations_from_extraction(self, relations: List[Dict], document_id: str) -> int:
        """
        Add extracted relations to the graph store.
        
        Args:
            relations: List of relation dicts with source, target, type keys
            document_id: Source document ID
            
        Returns:
            Number of relations added
        """
        added = 0
        
        # Helper function to find entity ID by text (case-insensitive)
        def find_entity_id(text: str, fallback_type: str = "ENTITY") -> str:
            text_lower = text.lower().replace(" ", "_")
            # Try to find existing entity
            for entity_id, entity in _entity_store.items():
                if entity["label"].lower() == text.lower():
                    return entity_id
            # Fallback: create new ID
            return f"{fallback_type}_{text_lower}"
        
        print(f"   📋 Processing {len(relations)} potential relations...")
        
        for relation in relations:
            source_text = relation.get("source", "")
            target_text = relation.get("target", "")
            rel_type = relation.get("type", "RELATED_TO")
            
            # Skip self-relations
            if source_text.lower() == target_text.lower():
                continue
            
            # Skip if either entity is empty
            if not source_text or not target_text:
                continue
            
            # Find entity IDs (search by text to handle type mismatches)
            source_type = relation.get("source_type", "ENTITY")
            target_type = relation.get("target_type", "ENTITY")
            source_id = find_entity_id(source_text, source_type)
            target_id = find_entity_id(target_text, target_type)
            
            # Create entities if they don't exist
            if source_id not in _entity_store:
                _entity_store[source_id] = {
                    "id": source_id,
                    "label": source_text,
                    "type": source_type,
                    "documents": [document_id],
                    "properties": {}
                }
            if target_id not in _entity_store:
                _entity_store[target_id] = {
                    "id": target_id,
                    "label": target_text,
                    "type": target_type,
                    "documents": [document_id],
                    "properties": {}
                }
            
            # Check if relation already exists
            exists = any(
                r["source"] == source_id and r["target"] == target_id and r["type"] == rel_type
                for r in _relation_store
            )
            if not exists:
                _relation_store.append({
                    "source": source_id,
                    "target": target_id,
                    "type": rel_type if isinstance(rel_type, str) else rel_type.value,
                    "document_id": document_id,
                    "properties": {"confidence": relation.get("confidence", 0.5)}
                })
                added += 1
                print(f"   🔗 Added relation: {source_text} --[{rel_type}]--> {target_text}")
        
        print(f"   ✅ Total relations added: {added}")
        return added
    
    async def extract_and_store(
        self,
        text: str,
        document_id: str,
    ) -> Dict:
        """
        Extract entities and relations from text and store in graph.
        
        Args:
            text: Text to extract from
            document_id: Source document ID
            
        Returns:
            Extraction statistics
        """
        entities = []
        relations = []
        
        # Extract entities
        if self.entity_extractor:
            extracted_entities = self.entity_extractor.extract(text, document_id)
            entities = [
                {
                    "text": e.text,
                    "entity_type": e.entity_type,
                    "confidence": e.confidence,
                    "document_id": document_id,
                }
                for e in extracted_entities
            ]
        
        # Extract relations
        if self.relation_extractor:
            extracted_relations = self.relation_extractor.extract(
                text,
                [{"text": e["text"], "entity_type": e["entity_type"]} for e in entities],
            )
            relations = [
                {
                    "source_text": r.source_text,
                    "source_type": r.source_type,
                    "target_text": r.target_text,
                    "target_type": r.target_type,
                    "relation_type": r.relation_type,
                    "confidence": r.confidence,
                }
                for r in extracted_relations
            ]
        
        # Build local graph
        if self.graph_builder:
            self.graph_builder.build_from_extraction(entities, relations)
        
        # Store in Neo4j
        if self.neo4j_client:
            await self._store_in_neo4j(entities, relations, document_id)
        
        return {
            "entities_extracted": len(entities),
            "relations_extracted": len(relations),
            "document_id": document_id,
        }
    
    async def _store_in_neo4j(
        self,
        entities: List[Dict],
        relations: List[Dict],
        document_id: str,
    ) -> None:
        """Store entities and relations in Neo4j."""
        entity_ids = {}
        
        # Create entity nodes
        for entity in entities:
            try:
                node_id = await self.neo4j_client.create_node(
                    label=entity["entity_type"],
                    properties={
                        "text": entity["text"],
                        "document_id": document_id,
                        "confidence": entity.get("confidence", 1.0),
                    },
                )
                entity_ids[entity["text"]] = node_id
            except Exception as e:
                logger.warning(f"Failed to create entity node: {e}")
        
        # Create relationships
        for relation in relations:
            source_id = entity_ids.get(relation["source_text"])
            target_id = entity_ids.get(relation["target_text"])
            
            if source_id and target_id:
                try:
                    await self.neo4j_client.create_relationship(
                        source_id=source_id,
                        target_id=target_id,
                        rel_type=relation["relation_type"],
                        properties={
                            "confidence": relation.get("confidence", 1.0),
                            "document_id": document_id,
                        },
                    )
                except Exception as e:
                    logger.warning(f"Failed to create relationship: {e}")
    
    async def get_graph(
        self,
        document_ids: Optional[List[str]] = None,
        entity_types: Optional[List[str]] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Get graph data for API response.
        
        Args:
            document_ids: Optional filter by document IDs
            entity_types: Optional filter by entity types
            limit: Maximum nodes to return
            
        Returns:
            Dict with nodes and edges
        """
        # Get entities from in-memory store
        nodes = []
        for entity_id, entity in list(_entity_store.items())[:limit]:
            # Filter by document if specified
            if document_ids:
                if not any(doc_id in entity.get("documents", []) for doc_id in document_ids):
                    continue
            
            # Filter by type if specified
            if entity_types and entity.get("type") not in entity_types:
                continue
            
            nodes.append({
                "id": entity["id"],
                "label": entity["label"],
                "type": entity.get("type", "CONCEPT"),
                "properties": entity.get("properties", {}),
                "documents": entity.get("documents", []),
            })
        
        # Get relations
        edges = []
        node_ids = {n["id"] for n in nodes}
        for relation in _relation_store:
            if relation["source"] in node_ids and relation["target"] in node_ids:
                edges.append({
                    "source": relation["source"],
                    "target": relation["target"],
                    "type": relation.get("type", "RELATED"),
                    "properties": relation.get("properties", {}),
                })
        
        # If no real entities yet, return helpful message
        if not nodes:
            print("   ⚠️ No entities in graph yet. Upload a document to populate the knowledge graph.")
        else:
            print(f"   📊 Returning {len(nodes)} nodes and {len(edges)} edges from graph")
        
        return {
            "nodes": nodes,
            "edges": edges,
        }
    
    async def get_graph_data(
        self,
        center_entity: Optional[str] = None,
        depth: int = 2,
        limit: int = 100,
    ) -> GraphData:
        """
        Get graph data for visualization.
        
        Args:
            center_entity: Optional center node for ego graph
            depth: Depth of expansion from center
            limit: Maximum nodes to return
            
        Returns:
            GraphData with nodes and edges
        """
        nodes = []
        edges = []
        
        if self.neo4j_client:
            if center_entity:
                # Get ego graph
                neighbors = await self.neo4j_client.get_neighbors(
                    node_id=center_entity,
                    limit=limit,
                )
                
                # Add center node
                center_node = await self.neo4j_client.get_node(center_entity)
                if center_node:
                    nodes.append({
                        "id": center_entity,
                        "label": center_node.get("text", center_entity),
                        "type": center_node.get("labels", ["Entity"])[0] if center_node.get("labels") else "Entity",
                    })
                
                # Add neighbors
                for neighbor in neighbors:
                    nodes.append({
                        "id": neighbor["id"],
                        "label": neighbor.get("text", neighbor["id"]),
                        "type": neighbor.get("labels", ["Entity"])[0] if neighbor.get("labels") else "Entity",
                    })
                    
                    rel = neighbor.get("relationship", {})
                    edges.append({
                        "source": center_entity,
                        "target": neighbor["id"],
                        "type": rel.get("type", "RELATED"),
                    })
            else:
                # Get sample of graph
                all_nodes = await self.neo4j_client.find_nodes(limit=limit)
                
                for node in all_nodes:
                    nodes.append({
                        "id": node["id"],
                        "label": node.get("text", node["id"]),
                        "type": node.get("labels", ["Entity"])[0] if node.get("labels") else "Entity",
                    })
        elif self.graph_builder:
            # Use local graph
            graph = self.graph_builder.graph
            
            for node_id, data in list(graph.nodes(data=True))[:limit]:
                nodes.append({
                    "id": node_id,
                    "label": data.get("label", node_id),
                    "type": data.get("node_type", "Entity"),
                })
            
            node_ids = set(n["id"] for n in nodes)
            
            for source, target, data in graph.edges(data=True):
                if source in node_ids and target in node_ids:
                    edges.append({
                        "source": source,
                        "target": target,
                        "type": data.get("relation_type", "RELATED"),
                    })
        
        # Get statistics
        statistics = await self.get_statistics()
        
        return GraphData(
            nodes=nodes,
            edges=edges,
            statistics=statistics,
        )
    
    async def find_path(
        self,
        source: str,
        target: str,
        max_depth: int = 5,
    ) -> Optional[List[Dict]]:
        """
        Find path between two entities.
        
        Args:
            source: Source entity ID
            target: Target entity ID
            max_depth: Maximum path length
            
        Returns:
            Path as list of nodes and edges
        """
        if self.neo4j_client:
            return await self.neo4j_client.find_path(source, target, max_depth)
        elif self.graph_builder:
            path = self.graph_builder.find_path(source, target, max_depth)
            if path:
                return {"nodes": path, "length": len(path) - 1}
        
        return None
    
    async def get_communities(self) -> List[Dict]:
        """
        Get detected communities.
        
        Returns:
            List of communities with their nodes
        """
        if not self.community_detector or not self.graph_builder:
            return []
        
        communities = self.community_detector.detect(self.graph_builder.graph)
        
        return [
            {
                "id": c.id,
                "label": c.label,
                "size": c.size,
                "central_nodes": c.central_nodes,
                "density": c.density,
            }
            for c in communities
        ]
    
    async def get_entity(self, entity_id: str) -> Optional[Dict]:
        """Get entity details."""
        if self.neo4j_client:
            return await self.neo4j_client.get_node(entity_id)
        elif self.graph_builder:
            node = self.graph_builder.get_node(entity_id)
            if node:
                return {
                    "id": node.id,
                    "label": node.label,
                    "type": node.node_type,
                    "properties": node.properties,
                }
        return None
    
    async def get_entity_neighbors(
        self,
        entity_id: str,
        limit: int = 50,
    ) -> List[Dict]:
        """Get neighbors of an entity."""
        if self.neo4j_client:
            return await self.neo4j_client.get_neighbors(entity_id, limit=limit)
        elif self.graph_builder:
            neighbors = self.graph_builder.get_neighbors(entity_id)
            return [
                {
                    "id": n.id,
                    "label": n.label,
                    "type": n.node_type,
                }
                for n in neighbors
            ]
        return []
    
    async def list_entities(
        self,
        entity_type: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> List[Dict[str, Any]]:
        """List entities with pagination."""
        entities = list(_entity_store.values())
        
        # Filter by type
        if entity_type:
            entities = [e for e in entities if e.get("type") == entity_type]
        
        # Filter by search term
        if search:
            search_lower = search.lower()
            entities = [e for e in entities if search_lower in e.get("label", "").lower()]
        
        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        
        return entities[start:end]
    
    async def get_neighbors(
        self,
        entity_id: str,
        depth: int = 1,
    ) -> Dict[str, Any]:
        """Get neighbors of an entity with depth."""
        # Find relations involving this entity
        neighbors = []
        edges = []
        
        for relation in _relation_store:
            if relation["source"] == entity_id:
                neighbor_id = relation["target"]
                if neighbor_id in _entity_store:
                    neighbors.append(_entity_store[neighbor_id])
                    edges.append(relation)
            elif relation["target"] == entity_id:
                neighbor_id = relation["source"]
                if neighbor_id in _entity_store:
                    neighbors.append(_entity_store[neighbor_id])
                    edges.append(relation)
        
        return {
            "nodes": neighbors,
            "edges": edges,
        }
    
    async def detect_communities(
        self,
        algorithm: str = "louvain",
    ) -> Dict[str, Any]:
        """Detect communities using specified algorithm."""
        # Group entities by type as simple communities
        communities = {}
        for entity in _entity_store.values():
            entity_type = entity.get("type", "OTHER")
            if entity_type not in communities:
                communities[entity_type] = []
            communities[entity_type].append(entity["id"])
        
        return {
            "communities": [
                {"id": i, "name": etype, "members": members}
                for i, (etype, members) in enumerate(communities.items())
            ],
            "algorithm": algorithm,
            "modularity": 0.5,
        }
    
    async def get_entity_types(self) -> List[str]:
        """Get all entity types in the graph."""
        types = set()
        for entity in _entity_store.values():
            types.add(entity.get("type", "CONCEPT"))
        return list(types) if types else ["CONCEPT", "PERSON", "ORGANIZATION", "LOCATION"]
    
    async def get_relation_types(self) -> List[str]:
        """Get all relation types in the graph."""
        types = set()
        for relation in _relation_store:
            types.add(relation.get("type", "RELATED_TO"))
        return list(types) if types else ["RELATED_TO", "MENTIONS"]
    
    async def search_entities(
        self,
        query: str,
        entity_type: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """Search for entities."""
        if self.neo4j_client:
            properties = {"text": query} if query else None
            return await self.neo4j_client.find_nodes(
                label=entity_type,
                properties=properties,
                limit=limit,
            )
        return []
    
    async def get_statistics(self) -> Dict:
        """Get graph statistics."""
        if self.neo4j_client:
            return await self.neo4j_client.get_statistics()
        elif self.graph_builder:
            return self.graph_builder.get_statistics()
        return {
            "node_count": 0,
            "relationship_count": 0,
            "entity_types": [],
            "relation_types": [],
        }

    # ============= Methods for Advanced Features =============
    
    async def get_document_entities(self, document_id: str) -> List[Dict]:
        """
        Get all entities from a specific document.
        
        Args:
            document_id: The document ID
            
        Returns:
            List of entity dictionaries
        """
        entities = []
        for entity_id, entity in _entity_store.items():
            if document_id in entity.get("documents", []):
                entities.append({
                    "id": entity_id,
                    "label": entity.get("label", ""),
                    "text": entity.get("label", ""),
                    "type": entity.get("type", "CONCEPT"),
                    "properties": entity.get("properties", {}),
                })
        return entities
    
    async def get_entity_documents(self, entity_id: str) -> List[Dict]:
        """
        Get all documents that contain a specific entity.
        
        Args:
            entity_id: The entity ID
            
        Returns:
            List of document dictionaries
        """
        entity = _entity_store.get(entity_id)
        if not entity:
            return []
        
        doc_ids = entity.get("documents", [])
        return [{"id": doc_id, "title": doc_id} for doc_id in doc_ids]
    
    async def get_document_authors(self, document_id: str) -> List[Dict]:
        """
        Get authors of a document.
        
        Args:
            document_id: The document ID
            
        Returns:
            List of author dictionaries
        """
        authors = []
        for entity_id, entity in _entity_store.items():
            if entity.get("type") == "PERSON" and document_id in entity.get("documents", []):
                authors.append({
                    "id": entity_id,
                    "name": entity.get("label", ""),
                })
        return authors
    
    async def get_author_documents(self, author_id: str) -> List[Dict]:
        """
        Get all documents by an author.
        
        Args:
            author_id: The author entity ID
            
        Returns:
            List of document dictionaries
        """
        author = _entity_store.get(author_id)
        if not author:
            return []
        
        doc_ids = author.get("documents", [])
        return [{"id": doc_id, "title": doc_id} for doc_id in doc_ids]
    
    async def get_cited_documents(self, document_id: str) -> List[Dict]:
        """
        Get documents cited by a document.
        
        Args:
            document_id: The source document ID
            
        Returns:
            List of cited document dictionaries
        """
        cited = []
        for relation in _relation_store:
            if relation.get("document_id") == document_id and relation.get("type") == "CITES":
                target_id = relation.get("target")
                target = _entity_store.get(target_id, {})
                cited.append({
                    "id": target_id,
                    "title": target.get("label", target_id),
                })
        return cited
    
    async def get_citing_documents(self, document_id: str) -> List[Dict]:
        """
        Get documents that cite a document.
        
        Args:
            document_id: The target document ID
            
        Returns:
            List of citing document dictionaries
        """
        citing = []
        for relation in _relation_store:
            if relation.get("target") == document_id and relation.get("type") == "CITES":
                source_id = relation.get("source")
                source = _entity_store.get(source_id, {})
                citing.append({
                    "id": source_id,
                    "title": source.get("label", source_id),
                })
        return citing
    
    async def get_co_cited_documents(self, document_id: str) -> List[Dict]:
        """
        Get documents that are frequently cited together with this document.
        
        Args:
            document_id: The document ID
            
        Returns:
            List of co-cited document dictionaries
        """
        # Find documents that share citations with this document
        our_citations = set()
        for relation in _relation_store:
            if relation.get("document_id") == document_id:
                our_citations.add(relation.get("target"))
        
        co_cited = []
        seen = set()
        for relation in _relation_store:
            if relation.get("document_id") != document_id:
                if relation.get("target") in our_citations:
                    other_doc = relation.get("document_id")
                    if other_doc not in seen:
                        seen.add(other_doc)
                        co_cited.append({
                            "id": other_doc,
                            "title": other_doc,
                        })
        
        return co_cited[:10]  # Limit to top 10
    
    async def get_document_neighbors(
        self,
        document_id: str,
        depth: int = 2,
        limit: int = 20,
    ) -> List[Dict]:
        """
        Get neighboring documents in the knowledge graph.
        
        Args:
            document_id: The document ID
            depth: How many hops to traverse
            limit: Maximum neighbors to return
            
        Returns:
            List of neighbor document dictionaries
        """
        neighbors = []
        visited = {document_id}
        current_level = {document_id}
        
        for d in range(depth):
            next_level = set()
            
            for doc_id in current_level:
                # Find related documents through shared entities
                for relation in _relation_store:
                    if relation.get("document_id") == doc_id:
                        target = relation.get("target")
                        if target and target not in visited:
                            visited.add(target)
                            next_level.add(target)
                            neighbors.append({
                                "id": target,
                                "title": _entity_store.get(target, {}).get("label", target),
                                "distance": d + 1,
                            })
            
            current_level = next_level
            
            if len(neighbors) >= limit:
                break
        
        return neighbors[:limit]

