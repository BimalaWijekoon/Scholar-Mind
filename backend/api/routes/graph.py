"""
Knowledge Graph API Routes
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from backend.api.dependencies import get_graph_service
from backend.services.graph_service import GraphService


router = APIRouter()


class NodeData(BaseModel):
    """Node data model."""
    id: str
    label: str
    type: str
    properties: dict


class EdgeData(BaseModel):
    """Edge data model."""
    source: str
    target: str
    type: str
    properties: Optional[dict] = None


class GraphData(BaseModel):
    """Graph data model."""
    nodes: List[NodeData]
    edges: List[EdgeData]


class EntityResponse(BaseModel):
    """Entity response model."""
    id: str
    name: str
    type: str
    document_count: int
    related_entities: List[dict]


class PathResponse(BaseModel):
    """Path between entities response."""
    path: List[NodeData]
    edges: List[EdgeData]
    total_paths: int


@router.get("/", response_model=GraphData)
async def get_graph(
    document_ids: Optional[List[str]] = Query(None),
    entity_types: Optional[List[str]] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    graph_service: GraphService = Depends(get_graph_service),
):
    """
    Get the knowledge graph data for visualization.
    
    Can filter by document IDs and entity types.
    """
    result = await graph_service.get_graph(
        document_ids=document_ids,
        entity_types=entity_types,
        limit=limit,
    )
    return result


@router.get("/entities", response_model=List[EntityResponse])
async def list_entities(
    entity_type: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    graph_service: GraphService = Depends(get_graph_service),
):
    """List all entities in the knowledge graph."""
    result = await graph_service.list_entities(
        entity_type=entity_type,
        search=search,
        page=page,
        page_size=page_size,
    )
    return result


@router.get("/entities/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: str,
    graph_service: GraphService = Depends(get_graph_service),
):
    """Get details of a specific entity."""
    result = await graph_service.get_entity(entity_id)
    if not result:
        raise HTTPException(status_code=404, detail="Entity not found")
    return result


@router.get("/entities/{entity_id}/neighbors", response_model=GraphData)
async def get_entity_neighbors(
    entity_id: str,
    depth: int = Query(1, ge=1, le=3),
    graph_service: GraphService = Depends(get_graph_service),
):
    """Get neighboring entities of a specific entity."""
    result = await graph_service.get_neighbors(entity_id, depth=depth)
    return result


@router.get("/path", response_model=PathResponse)
async def find_path(
    source_id: str,
    target_id: str,
    max_hops: int = Query(4, ge=1, le=6),
    graph_service: GraphService = Depends(get_graph_service),
):
    """Find paths between two entities."""
    result = await graph_service.find_path(
        source_id=source_id,
        target_id=target_id,
        max_hops=max_hops,
    )
    return result


@router.get("/communities")
async def get_communities(
    algorithm: str = Query("louvain", pattern="^(louvain|leiden|label_propagation)$"),
    graph_service: GraphService = Depends(get_graph_service),
):
    """Detect communities/clusters in the knowledge graph."""
    result = await graph_service.detect_communities(algorithm=algorithm)
    return result


@router.get("/statistics")
async def get_graph_statistics(
    graph_service: GraphService = Depends(get_graph_service),
):
    """Get statistics about the knowledge graph."""
    result = await graph_service.get_statistics()
    return result


@router.get("/entity-types")
async def get_entity_types(
    graph_service: GraphService = Depends(get_graph_service),
):
    """Get all entity types in the graph."""
    result = await graph_service.get_entity_types()
    return result


@router.get("/relation-types")
async def get_relation_types(
    graph_service: GraphService = Depends(get_graph_service),
):
    """Get all relation types in the graph."""
    result = await graph_service.get_relation_types()
    return result
