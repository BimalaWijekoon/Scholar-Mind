#!/usr/bin/env python
"""
Export Graph Script

This script exports the knowledge graph to various formats for backup,
analysis, or visualization in external tools.
"""

import asyncio
import logging
import argparse
import json
from pathlib import Path
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def export_to_json(output_path: str) -> dict:
    """
    Export knowledge graph to JSON format.
    
    Args:
        output_path: Path to output file
        
    Returns:
        Export statistics
    """
    from backend.core.knowledge_graph import Neo4jClient
    
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    
    client = Neo4jClient(
        uri=neo4j_uri,
        user=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password"),
    )
    
    await client.connect()
    
    try:
        # Export nodes
        logger.info("Exporting nodes...")
        nodes = await client.find_nodes(limit=100000)
        
        # Export relationships
        logger.info("Exporting relationships...")
        # Query all relationships
        async with client.driver.session() as session:
            result = await session.run("""
                MATCH (a)-[r]->(b)
                RETURN id(a) as source_id, id(b) as target_id, type(r) as type,
                       properties(r) as properties
                LIMIT 100000
            """)
            relationships = [
                {
                    "source": record["source_id"],
                    "target": record["target_id"],
                    "type": record["type"],
                    "properties": dict(record["properties"]) if record["properties"] else {},
                }
                async for record in result
            ]
        
        # Create export structure
        export_data = {
            "metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "node_count": len(nodes),
                "relationship_count": len(relationships),
            },
            "nodes": nodes,
            "relationships": relationships,
        }
        
        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Exported to {output_path}")
        
        return export_data["metadata"]
        
    finally:
        await client.close()


async def export_to_graphml(output_path: str) -> dict:
    """
    Export knowledge graph to GraphML format.
    
    Args:
        output_path: Path to output file
        
    Returns:
        Export statistics
    """
    import networkx as nx
    from backend.core.knowledge_graph import Neo4jClient
    
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    
    client = Neo4jClient(
        uri=neo4j_uri,
        user=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password"),
    )
    
    await client.connect()
    
    try:
        # Create NetworkX graph
        G = nx.DiGraph()
        
        # Add nodes
        logger.info("Exporting nodes...")
        nodes = await client.find_nodes(limit=100000)
        
        for node in nodes:
            G.add_node(node["id"], **{k: str(v) for k, v in node.items() if k != "id"})
        
        # Add edges
        logger.info("Exporting edges...")
        async with client.driver.session() as session:
            result = await session.run("""
                MATCH (a)-[r]->(b)
                RETURN a.id as source, b.id as target, type(r) as type
                LIMIT 100000
            """)
            async for record in result:
                G.add_edge(
                    record["source"],
                    record["target"],
                    type=record["type"],
                )
        
        # Write GraphML
        nx.write_graphml(G, output_path)
        
        logger.info(f"Exported to {output_path}")
        
        return {
            "exported_at": datetime.utcnow().isoformat(),
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
        }
        
    finally:
        await client.close()


async def export_to_csv(output_dir: str) -> dict:
    """
    Export knowledge graph to CSV files (nodes.csv and edges.csv).
    
    Args:
        output_dir: Directory for output files
        
    Returns:
        Export statistics
    """
    import csv
    from backend.core.knowledge_graph import Neo4jClient
    
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    
    client = Neo4jClient(
        uri=neo4j_uri,
        user=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password"),
    )
    
    await client.connect()
    
    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Export nodes
        logger.info("Exporting nodes...")
        nodes = await client.find_nodes(limit=100000)
        
        nodes_file = output_path / "nodes.csv"
        with open(nodes_file, "w", newline="", encoding="utf-8") as f:
            if nodes:
                writer = csv.DictWriter(f, fieldnames=nodes[0].keys())
                writer.writeheader()
                writer.writerows(nodes)
        
        # Export edges
        logger.info("Exporting edges...")
        edges_file = output_path / "edges.csv"
        
        async with client.driver.session() as session:
            result = await session.run("""
                MATCH (a)-[r]->(b)
                RETURN a.id as source, b.id as target, type(r) as type
                LIMIT 100000
            """)
            
            edges = [
                {
                    "source": record["source"],
                    "target": record["target"],
                    "type": record["type"],
                }
                async for record in result
            ]
        
        with open(edges_file, "w", newline="", encoding="utf-8") as f:
            if edges:
                writer = csv.DictWriter(f, fieldnames=["source", "target", "type"])
                writer.writeheader()
                writer.writerows(edges)
        
        logger.info(f"Exported to {output_dir}")
        
        return {
            "exported_at": datetime.utcnow().isoformat(),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "files": [str(nodes_file), str(edges_file)],
        }
        
    finally:
        await client.close()


async def export_to_cypher(output_path: str) -> dict:
    """
    Export knowledge graph to Cypher statements for reimport.
    
    Args:
        output_path: Path to output file
        
    Returns:
        Export statistics
    """
    from backend.core.knowledge_graph import Neo4jClient
    
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    
    client = Neo4jClient(
        uri=neo4j_uri,
        user=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password"),
    )
    
    await client.connect()
    
    try:
        statements = []
        
        # Export nodes
        logger.info("Generating node statements...")
        nodes = await client.find_nodes(limit=100000)
        
        for node in nodes:
            props = ", ".join(f'{k}: "{v}"' for k, v in node.items() if k != "labels")
            labels = ":".join(node.get("labels", ["Entity"]))
            statements.append(f"CREATE (:{labels} {{{props}}})")
        
        # Export relationships
        logger.info("Generating relationship statements...")
        async with client.driver.session() as session:
            result = await session.run("""
                MATCH (a)-[r]->(b)
                RETURN a.id as source, b.id as target, type(r) as type
                LIMIT 100000
            """)
            
            async for record in result:
                statements.append(
                    f'MATCH (a {{id: "{record["source"]}"}}), (b {{id: "{record["target"]}"}}) '
                    f'CREATE (a)-[:{record["type"]}]->(b)'
                )
        
        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("// Generated Cypher export\n")
            f.write(f"// Exported at: {datetime.utcnow().isoformat()}\n\n")
            for stmt in statements:
                f.write(stmt + ";\n")
        
        logger.info(f"Exported to {output_path}")
        
        return {
            "exported_at": datetime.utcnow().isoformat(),
            "statement_count": len(statements),
        }
        
    finally:
        await client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export Knowledge Graph")
    parser.add_argument("output", help="Output file or directory path")
    parser.add_argument(
        "--format", "-f",
        choices=["json", "graphml", "csv", "cypher"],
        default="json",
        help="Export format (default: json)"
    )
    args = parser.parse_args()
    
    format_handlers = {
        "json": export_to_json,
        "graphml": export_to_graphml,
        "csv": export_to_csv,
        "cypher": export_to_cypher,
    }
    
    handler = format_handlers[args.format]
    result = asyncio.run(handler(args.output))
    
    print("\nExport completed!")
    print(json.dumps(result, indent=2))
