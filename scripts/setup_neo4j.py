#!/usr/bin/env python
"""
Neo4j Setup Script

This script sets up the Neo4j database with required constraints, indexes,
and initial configuration for the ScholarMind knowledge graph.
"""

import asyncio
import logging
from neo4j import AsyncGraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j connection settings
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


# Constraints and indexes to create
CONSTRAINTS = [
    # Unique constraints
    "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
    "CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
    "CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",
    "CREATE CONSTRAINT organization_id IF NOT EXISTS FOR (o:Organization) REQUIRE o.id IS UNIQUE",
]

INDEXES = [
    # Text indexes for full-text search
    "CREATE FULLTEXT INDEX entity_text IF NOT EXISTS FOR (e:Entity) ON EACH [e.text, e.label]",
    "CREATE FULLTEXT INDEX document_text IF NOT EXISTS FOR (d:Document) ON EACH [d.title, d.abstract]",
    
    # Regular indexes for common queries
    "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
    "CREATE INDEX entity_document IF NOT EXISTS FOR (e:Entity) ON (e.document_id)",
    "CREATE INDEX document_status IF NOT EXISTS FOR (d:Document) ON (d.status)",
]


async def setup_neo4j():
    """Set up Neo4j database with constraints and indexes."""
    
    logger.info(f"Connecting to Neo4j at {NEO4J_URI}")
    
    driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        async with driver.session() as session:
            # Verify connection
            result = await session.run("RETURN 1 AS test")
            record = await result.single()
            if record["test"] == 1:
                logger.info("Successfully connected to Neo4j")
            
            # Create constraints
            logger.info("Creating constraints...")
            for constraint in CONSTRAINTS:
                try:
                    await session.run(constraint)
                    logger.info(f"Created constraint: {constraint[:50]}...")
                except Exception as e:
                    logger.warning(f"Constraint may already exist: {e}")
            
            # Create indexes
            logger.info("Creating indexes...")
            for index in INDEXES:
                try:
                    await session.run(index)
                    logger.info(f"Created index: {index[:50]}...")
                except Exception as e:
                    logger.warning(f"Index may already exist: {e}")
            
            # Verify setup
            result = await session.run("SHOW CONSTRAINTS")
            constraints = [record async for record in result]
            logger.info(f"Total constraints: {len(constraints)}")
            
            result = await session.run("SHOW INDEXES")
            indexes = [record async for record in result]
            logger.info(f"Total indexes: {len(indexes)}")
            
            logger.info("Neo4j setup completed successfully!")
            
    finally:
        await driver.close()


async def clear_database():
    """Clear all data from the database (use with caution!)."""
    
    logger.warning("Clearing all data from Neo4j database...")
    
    driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        async with driver.session() as session:
            # Delete all nodes and relationships
            await session.run("MATCH (n) DETACH DELETE n")
            logger.info("All data cleared from database")
    finally:
        await driver.close()


async def get_statistics():
    """Get database statistics."""
    
    driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        async with driver.session() as session:
            # Count nodes
            result = await session.run("MATCH (n) RETURN count(n) as count")
            record = await result.single()
            node_count = record["count"]
            
            # Count relationships
            result = await session.run("MATCH ()-[r]->() RETURN count(r) as count")
            record = await result.single()
            rel_count = record["count"]
            
            # Count by label
            result = await session.run("""
                CALL db.labels() YIELD label
                CALL apoc.cypher.run('MATCH (n:`' + label + '`) RETURN count(n) as count', {})
                YIELD value
                RETURN label, value.count as count
            """)
            labels = {}
            async for record in result:
                labels[record["label"]] = record["count"]
            
            print(f"\nNeo4j Database Statistics")
            print(f"{'=' * 40}")
            print(f"Total nodes: {node_count}")
            print(f"Total relationships: {rel_count}")
            print(f"\nNodes by label:")
            for label, count in labels.items():
                print(f"  {label}: {count}")
            
    finally:
        await driver.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Neo4j Setup Script")
    parser.add_argument("--clear", action="store_true", help="Clear all data")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    args = parser.parse_args()
    
    if args.clear:
        response = input("Are you sure you want to clear all data? (yes/no): ")
        if response.lower() == "yes":
            asyncio.run(clear_database())
        else:
            print("Cancelled.")
    elif args.stats:
        asyncio.run(get_statistics())
    else:
        asyncio.run(setup_neo4j())
