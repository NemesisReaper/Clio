"""Graph schema definitions, constraints, and Cypher statement templates."""
from typing import Dict, List, Set
from clio.models.graph import NodeType, RelationType

# Allowed Node Labels
VALID_NODE_LABELS: Set[str] = {nt.value for nt in NodeType}

# Allowed Relationship Types
VALID_RELATIONSHIPS: Set[str] = {rt.value for rt in RelationType}

# Constraints definition to ensure idempotency and unique IDs in Neo4j
SCHEMA_CONSTRAINTS = [
    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE;"
    for label in VALID_NODE_LABELS
]

# Cypher Templates for Idempotent Ingestion
CYPHER_UPSERT_NODE = """
MERGE (n:{label} {id: $id})
ON CREATE SET
    n.name = $name,
    n.type = $type,
    n.verification_status = $verification_status,
    n.source_reference = $source_reference,
    n.created_at = datetime($created_at),
    n += $properties
ON MATCH SET
    n.name = $name,
    n.verification_status = $verification_status,
    n += $properties
RETURN n.id AS id;
"""

CYPHER_UPSERT_RELATIONSHIP = """
MATCH (source {id: $source_id})
MATCH (target {id: $target_id})
MERGE (source)-[r:{rel_type} {id: $rel_id}]->(target)
ON CREATE SET
    r.confidence = $confidence,
    r.verification_status = $verification_status,
    r.source_document_id = $source_document_id,
    r.source_page_number = $source_page_number,
    r.evidence_id = $evidence_id,
    r += $properties
ON MATCH SET
    r.confidence = $confidence,
    r.verification_status = $verification_status,
    r += $properties
RETURN r.id AS id;
"""

CYPHER_MIDDLE_OUT_TRAVERSAL = """
MATCH (anchor {id: $anchor_id})
CALL apoc.path.subgraphAll(anchor, {
    maxLevel: $max_depth,
    relationshipFilter: $rel_filter,
    labelFilter: $label_filter
})
YIELD nodes, relationships
RETURN nodes, relationships;
"""

