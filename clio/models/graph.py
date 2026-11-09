"""Graph schema definitions, node types, relationships, and traversal models."""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    DOCUMENT = "Document"
    PAGE = "Page"
    CHAKRA = "Chakra"
    SHLOKA = "Shloka"
    PASSAGE = "Passage"
    TERM = "Term"
    CONCEPT = "Concept"
    PERSON = "Person"
    WORK = "Work"
    LANGUAGE = "Language"
    SOURCE = "Source"
    EVIDENCE = "Evidence"
    HYPOTHESIS = "Hypothesis"


class RelationType(str, Enum):
    CONTAINS_PAGE = "CONTAINS_PAGE"
    CONTAINS_CHAKRA = "CONTAINS_CHAKRA"
    CONTAINS_SHLOKA = "CONTAINS_SHLOKA"
    HAS_PASSAGE = "HAS_PASSAGE"
    CONTAINS_TERM = "CONTAINS_TERM"
    REFERS_TO = "REFERS_TO"
    DISCUSSES = "DISCUSSES"
    HAS_VARIANT = "HAS_VARIANT"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    SUPPORTED_BY = "SUPPORTED_BY"
    DERIVED_FROM = "DERIVED_FROM"


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    PROPOSED = "PROPOSED"
    CONTESTED = "CONTESTED"


class GraphNode(BaseModel):
    """Generic Node representation in the historical knowledge graph."""
    id: str
    type: NodeType
    name: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    source_reference: Optional[str] = None
    verification_status: VerificationStatus = VerificationStatus.VERIFIED
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GraphRelationship(BaseModel):
    """Directed relationship between graph entities with provenance."""
    id: str
    source_id: str
    target_id: str
    type: RelationType
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    verification_status: VerificationStatus = VerificationStatus.VERIFIED
    source_document_id: Optional[str] = None
    source_page_number: Optional[int] = None
    evidence_id: Optional[str] = None


class TraversalRequest(BaseModel):
    """Request payload for middle-out graph traversal."""
    anchor_id: str = Field(..., description="ID of entity to expand middle-out from")
    max_depth: int = Field(3, ge=1, le=5, description="Maximum traversal depth (default: 3, bound: 1-5)")
    relationship_types: Optional[List[RelationType]] = Field(
        None,
        description="Optional whitelist of relationship types to follow"
    )
    start_year: Optional[int] = Field(None, description="Optional historical start year for temporal filtering")
    end_year: Optional[int] = Field(None, description="Optional historical end year for temporal filtering")
    direction: str = Field("BOTH", description="Traversal direction: OUTGOING, INCOMING, or BOTH")
    include_hypotheses: bool = Field(True, description="Whether to include unverified/proposed hypothesis nodes")


class TraversalPath(BaseModel):
    """A sequence of nodes and relationships traversed."""
    node_ids: List[str]
    relationship_types: List[RelationType]
    depth: int


class TraversalResult(BaseModel):
    """Middle-out traversal response."""
    anchor_entity: GraphNode
    connected_entities: List[GraphNode]
    relationships: List[GraphRelationship]
    paths: List[TraversalPath] = Field(default_factory=list)
    total_nodes: int
    total_relationships: int

