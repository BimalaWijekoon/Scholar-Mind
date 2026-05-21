// ============================================
// ScholarMind — Neo4j Schema & Constraints
// Run after database creation:
//   cat neo4j_schema.cypher | cypher-shell -u neo4j -p scholarmind123
// ============================================

// --- Uniqueness Constraints ---
CREATE CONSTRAINT entity_text_unique IF NOT EXISTS
FOR (e:Entity) REQUIRE e.text IS UNIQUE;

CREATE CONSTRAINT document_id_unique IF NOT EXISTS
FOR (d:Document) REQUIRE d.document_id IS UNIQUE;

CREATE CONSTRAINT author_name_unique IF NOT EXISTS
FOR (a:Author) REQUIRE a.name IS UNIQUE;

CREATE CONSTRAINT concept_text_unique IF NOT EXISTS
FOR (c:Concept) REQUIRE c.text IS UNIQUE;

// --- Indexes for frequent lookups ---
CREATE INDEX entity_type_idx IF NOT EXISTS
FOR (e:Entity) ON (e.entity_type);

CREATE INDEX entity_document_idx IF NOT EXISTS
FOR (e:Entity) ON (e.document_id);

CREATE INDEX entity_confidence_idx IF NOT EXISTS
FOR (e:Entity) ON (e.confidence);

CREATE INDEX document_status_idx IF NOT EXISTS
FOR (d:Document) ON (d.status);

// --- Full-text search index ---
CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS
FOR (e:Entity) ON EACH [e.text, e.description];

// --- Relationship property indexes ---
CREATE INDEX rel_confidence_idx IF NOT EXISTS
FOR ()-[r:RELATED_TO]-() ON (r.confidence);

CREATE INDEX rel_document_idx IF NOT EXISTS
FOR ()-[r:RELATED_TO]-() ON (r.document_id);
