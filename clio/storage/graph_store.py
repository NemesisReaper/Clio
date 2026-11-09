"""Graph storage engine supporting both Neo4j and an in-memory NetworkX property graph.

Provides middle-out bidirectional graph traversal with depth limiting,
provenance preservation, cycle prevention, and temporal filtering.
"""
import socket
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional, Set
import networkx as nx
from neo4j import GraphDatabase, Driver

from clio.config import settings
from clio.models.graph import (
    GraphNode,
    GraphRelationship,
    NodeType,
    RelationType,
    TraversalPath,
    TraversalRequest,
    TraversalResult,
    VerificationStatus,
)
from clio.graph.schema import (
    CYPHER_UPSERT_NODE,
    CYPHER_UPSERT_RELATIONSHIP,
    SCHEMA_CONSTRAINTS,
    VALID_NODE_LABELS,
    VALID_RELATIONSHIPS,
)

logger = logging.getLogger(__name__)


def _is_service_reachable(host: str, port: int, timeout: float = 0.2) -> bool:
    """Fast check whether remote database port is accepting connections."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


class GraphStore:
    """Historical Knowledge Graph store with Neo4j driver and in-memory fallback."""

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        force_in_memory: bool = False,
    ):
        self.force_in_memory = force_in_memory
        self.driver: Optional[Driver] = None
        # Always maintain in-memory MultiDiGraph as robust fast fallback or mirror
        self.nx_graph: nx.MultiDiGraph = nx.MultiDiGraph()
        self.nodes_registry: Dict[str, GraphNode] = {}
        self.edges_registry: Dict[str, GraphRelationship] = {}

        if not force_in_memory:
            target_uri = uri or settings.neo4j_uri
            target_user = user or settings.neo4j_user
            target_pass = password or settings.neo4j_password

            # Parse host and port from uri (e.g. bolt://localhost:7687)
            import urllib.parse
            parsed = urllib.parse.urlparse(target_uri)
            host = parsed.hostname or "localhost"
            port = parsed.port or 7687

            if _is_service_reachable(host, port, timeout=0.2):
                try:
                    self.driver = GraphDatabase.driver(
                        target_uri,
                        auth=(target_user, target_pass),
                        connection_timeout=2.0,
                    )
                    self.driver.verify_connectivity()
                    logger.info("Connected to Neo4j instance at %s", target_uri)
                    self._apply_schema_constraints()
                except Exception as e:
                    logger.warning("Could not connect to Neo4j at %s: %s", target_uri, e)
                    self.driver = None
            else:
                logger.info(
                    "Neo4j is not listening at %s:%d. Using in-memory property graph.",
                    host,
                    port,
                )
                self.driver = None

    def _apply_schema_constraints(self) -> None:
        """Apply uniqueness constraints in Neo4j."""
        if not self.driver:
            return
        try:
            with self.driver.session(database=settings.neo4j_database) as session:
                for stmt in SCHEMA_CONSTRAINTS:
                    session.run(stmt)
        except Exception as e:
            logger.warning("Error applying Neo4j constraints: %s", e)

    def close(self) -> None:
        if self.driver:
            self.driver.close()

    def upsert_node(self, node: GraphNode) -> GraphNode:
        """Idempotently insert or update a graph node with provenance."""
        if node.type.value not in VALID_NODE_LABELS:
            raise ValueError(f"Invalid node label: {node.type.value}")

        # Update in-memory registry
        self.nodes_registry[node.id] = node
        self.nx_graph.add_node(
            node.id,
            id=node.id,
            type=node.type.value,
            name=node.name,
            verification_status=node.verification_status.value,
            source_reference=node.source_reference,
            created_at=node.created_at.isoformat(),
            **node.properties,
        )

        # Update Neo4j if connected
        if self.driver:
            query = CYPHER_UPSERT_NODE.format(label=node.type.value)
            try:
                with self.driver.session(database=settings.neo4j_database) as session:
                    session.run(
                        query,
                        id=node.id,
                        name=node.name,
                        type=node.type.value,
                        verification_status=node.verification_status.value,
                        source_reference=node.source_reference,
                        created_at=node.created_at.isoformat(),
                        properties=node.properties,
                    )
            except Exception as e:
                logger.error("Neo4j node upsert failed: %s", e)

        return node

    def upsert_relationship(self, rel: GraphRelationship) -> GraphRelationship:
        """Idempotently insert or update a directed relationship with provenance."""
        if rel.type.value not in VALID_RELATIONSHIPS:
            raise ValueError(f"Invalid relationship type: {rel.type.value}")

        if rel.source_id not in self.nodes_registry or rel.target_id not in self.nodes_registry:
            raise ValueError(
                f"Cannot link {rel.source_id} -> {rel.target_id}: one or both nodes missing"
            )

        self.edges_registry[rel.id] = rel
        self.nx_graph.add_edge(
            rel.source_id,
            rel.target_id,
            key=rel.id,
            id=rel.id,
            type=rel.type.value,
            confidence=rel.confidence,
            verification_status=rel.verification_status.value,
            source_document_id=rel.source_document_id,
            source_page_number=rel.source_page_number,
            evidence_id=rel.evidence_id,
            **rel.properties,
        )

        if self.driver:
            query = CYPHER_UPSERT_RELATIONSHIP.format(rel_type=rel.type.value)
            try:
                with self.driver.session(database=settings.neo4j_database) as session:
                    session.run(
                        query,
                        source_id=rel.source_id,
                        target_id=rel.target_id,
                        rel_id=rel.id,
                        confidence=rel.confidence,
                        verification_status=rel.verification_status.value,
                        source_document_id=rel.source_document_id,
                        source_page_number=rel.source_page_number,
                        evidence_id=rel.evidence_id,
                        properties=rel.properties,
                    )
            except Exception as e:
                logger.error("Neo4j relationship upsert failed: %s", e)

        return rel

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Fetch node by ID."""
        return self.nodes_registry.get(node_id)

    def traverse_middle_out(self, req: TraversalRequest) -> TraversalResult:
        """Execute middle-out graph traversal starting from an anchor entity."""
        if req.anchor_id not in self.nodes_registry:
            raise ValueError(f"Anchor entity '{req.anchor_id}' does not exist in graph")

        anchor_node = self.nodes_registry[req.anchor_id]
        max_depth = min(max(req.max_depth, 1), 5)  # Enforce bounds [1, 5]

        allowed_rel_types = (
            {rt.value for rt in req.relationship_types}
            if req.relationship_types
            else None
        )

        visited_nodes: Set[str] = {req.anchor_id}
        traversed_edges: Dict[str, GraphRelationship] = {}
        paths: List[TraversalPath] = []

        # Queue contains: (current_node_id, current_depth, current_path_nodes, current_path_rels)
        queue = [(req.anchor_id, 0, [req.anchor_id], [])]

        while queue:
            curr_id, depth, path_nodes, path_rels = queue.pop(0)

            if depth >= max_depth:
                continue

            # Gather candidate edges depending on direction
            candidate_edges = []

            # 1. Outgoing
            if req.direction in ("OUTGOING", "BOTH"):
                if self.nx_graph.has_node(curr_id):
                    for _, target, key, data in self.nx_graph.out_edges(curr_id, data=True, keys=True):
                        candidate_edges.append((curr_id, target, key, data, "OUT"))

            # 2. Incoming
            if req.direction in ("INCOMING", "BOTH"):
                if self.nx_graph.has_node(curr_id):
                    for source, _, key, data in self.nx_graph.in_edges(curr_id, data=True, keys=True):
                        candidate_edges.append((source, curr_id, key, data, "IN"))

            for src, tgt, key, data, edge_dir in candidate_edges:
                rel_type = data.get("type")
                if allowed_rel_types and rel_type not in allowed_rel_types:
                    continue

                neighbor_id = tgt if edge_dir == "OUT" else src
                rel_obj = self.edges_registry.get(key)
                if not rel_obj:
                    continue

                # Filter hypothesis nodes if requested
                neighbor_node = self.nodes_registry.get(neighbor_id)
                if not neighbor_node:
                    continue

                if not req.include_hypotheses:
                    if neighbor_node.type == NodeType.HYPOTHESIS:
                        continue
                    if rel_obj.verification_status == VerificationStatus.PROPOSED:
                        continue

                # Date range filter on entities/relationships
                year = neighbor_node.properties.get("year")
                if year is not None:
                    if req.start_year and year < req.start_year:
                        continue
                    if req.end_year and year > req.end_year:
                        continue

                traversed_edges[key] = rel_obj

                # Record traversal path
                new_path_nodes = path_nodes + [neighbor_id]
                new_path_rels = path_rels + [RelationType(rel_type)]
                paths.append(
                    TraversalPath(
                        node_ids=new_path_nodes,
                        relationship_types=new_path_rels,
                        depth=depth + 1,
                    )
                )

                if neighbor_id not in visited_nodes:
                    visited_nodes.add(neighbor_id)
                    queue.append((neighbor_id, depth + 1, new_path_nodes, new_path_rels))

        connected_nodes = [
            self.nodes_registry[nid]
            for nid in visited_nodes
            if nid != req.anchor_id
        ]

        return TraversalResult(
            anchor_entity=anchor_node,
            connected_entities=connected_nodes,
            relationships=list(traversed_edges.values()),
            paths=paths,
            total_nodes=len(visited_nodes),
            total_relationships=len(traversed_edges),
        )


# Global singleton instance (in-memory property graph enabled by default, auto-connects to Neo4j if available)
graph_store = GraphStore()
