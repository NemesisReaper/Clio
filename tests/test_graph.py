"""Unit tests for Historical Knowledge Graph, Middle-Out Traversal, and Hypothesis Guardrails."""
from datetime import datetime
import pytest
from clio.models.graph import (
    GraphNode,
    GraphRelationship,
    NodeType,
    RelationType,
    TraversalRequest,
    VerificationStatus,
)
from clio.storage.graph_store import GraphStore


@pytest.fixture
def clean_graph_store():
    """Create fresh isolated in-memory GraphStore."""
    store = GraphStore(force_in_memory=True)
    return store


def test_graph_node_and_relationship_types(clean_graph_store):
    """Verify that all node and relationship types can be created with provenance."""
    # Create Document node
    doc_node = GraphNode(
        id="doc_test_99",
        type=NodeType.DOCUMENT,
        name="Test Manuscript PDF",
        source_reference="sha256:abc12345",
        verification_status=VerificationStatus.VERIFIED,
    )
    clean_graph_store.upsert_node(doc_node)

    # Create Person node
    person_node = GraphNode(
        id="person_kumudendu_muni",
        type=NodeType.PERSON,
        name="Kumudendu Muni",
        properties={"year": 820},
        source_reference="Scholarly Editions",
        verification_status=VerificationStatus.VERIFIED,
    )
    clean_graph_store.upsert_node(person_node)

    # Create Work node
    work_node = GraphNode(
        id="work_siri_bhoovalaya",
        type=NodeType.WORK,
        name="Siri Bhoovalaya",
        properties={"year": 830},
        source_reference="Scholarly Editions",
        verification_status=VerificationStatus.VERIFIED,
    )
    clean_graph_store.upsert_node(work_node)

    # Create Relationship: Person -> REFERS_TO -> Work
    rel = GraphRelationship(
        id="rel_kumudendu_authored_work",
        source_id="person_kumudendu_muni",
        target_id="work_siri_bhoovalaya",
        type=RelationType.REFERS_TO,
        confidence=1.0,
        verification_status=VerificationStatus.VERIFIED,
        source_document_id="doc_test_99",
        source_page_number=1,
    )
    clean_graph_store.upsert_relationship(rel)

    assert clean_graph_store.get_node("person_kumudendu_muni") is not None
    assert clean_graph_store.get_node("work_siri_bhoovalaya") is not None


def test_idempotent_ingestion(clean_graph_store):
    """Verify that repeated ingestion of identical nodes does not duplicate them."""
    node = GraphNode(
        id="concept_bandha",
        type=NodeType.CONCEPT,
        name="Bandha",
        properties={"geometry": "Chitra-Kavya"},
    )
    # Upsert once
    clean_graph_store.upsert_node(node)
    count_1 = len(clean_graph_store.nodes_registry)

    # Upsert second time with modified property
    node_updated = GraphNode(
        id="concept_bandha",
        type=NodeType.CONCEPT,
        name="Bandha (Geometric Traversal)",
        properties={"geometry": "Chitra-Kavya Matrix Traversal"},
    )
    clean_graph_store.upsert_node(node_updated)
    count_2 = len(clean_graph_store.nodes_registry)

    assert count_1 == count_2
    assert clean_graph_store.get_node("concept_bandha").name == "Bandha (Geometric Traversal)"


def test_hypothesis_guardrails(clean_graph_store):
    """Verify that speculative hypotheses remain PROPOSED and are not promoted to facts."""
    ev_node = GraphNode(
        id="evidence_line_45",
        type=NodeType.EVIDENCE,
        name="Colophon Excerpt",
        properties={"quote": "Contains mention of 718 languages"},
        verification_status=VerificationStatus.VERIFIED,
    )
    clean_graph_store.upsert_node(ev_node)

    hyp_node = GraphNode(
        id="hyp_718_languages",
        type=NodeType.HYPOTHESIS,
        name="Claim of 718 encoded world languages",
        properties={"confidence": 0.45},
        verification_status=VerificationStatus.PROPOSED,
    )
    clean_graph_store.upsert_node(hyp_node)

    rel_hyp = GraphRelationship(
        id="rel_hyp_evidence",
        source_id="hyp_718_languages",
        target_id="evidence_line_45",
        type=RelationType.DERIVED_FROM,
        confidence=0.50,
        verification_status=VerificationStatus.PROPOSED,
    )
    clean_graph_store.upsert_relationship(rel_hyp)

    # When querying traversal without hypotheses, it should be excluded
    res_no_hyp = clean_graph_store.traverse_middle_out(
        TraversalRequest(
            anchor_id="evidence_line_45",
            max_depth=2,
            include_hypotheses=False,
        )
    )
    assert all(n.type != NodeType.HYPOTHESIS for n in res_no_hyp.connected_entities)

    # When querying with hypotheses, it is included with PROPOSED status
    res_with_hyp = clean_graph_store.traverse_middle_out(
        TraversalRequest(
            anchor_id="evidence_line_45",
            max_depth=2,
            include_hypotheses=True,
        )
    )
    assert any(n.type == NodeType.HYPOTHESIS for n in res_with_hyp.connected_entities)
    hyp_entity = [n for n in res_with_hyp.connected_entities if n.type == NodeType.HYPOTHESIS][0]
    assert hyp_entity.verification_status == VerificationStatus.PROPOSED


def test_middle_out_traversal_depth_and_cycle_prevention(clean_graph_store):
    """Verify bidirectional traversal, depth limiting (default 3), and cycle prevention."""
    # Create chain of nodes: A -> B -> C -> D -> A (cycle!)
    for name in ["A", "B", "C", "D"]:
        clean_graph_store.upsert_node(
            GraphNode(id=f"node_{name}", type=NodeType.CONCEPT, name=f"Node {name}")
        )

    clean_graph_store.upsert_relationship(
        GraphRelationship(
            id="rel_A_B", source_id="node_A", target_id="node_B", type=RelationType.REFERS_TO
        )
    )
    clean_graph_store.upsert_relationship(
        GraphRelationship(
            id="rel_B_C", source_id="node_B", target_id="node_C", type=RelationType.REFERS_TO
        )
    )
    clean_graph_store.upsert_relationship(
        GraphRelationship(
            id="rel_C_D", source_id="node_C", target_id="node_D", type=RelationType.REFERS_TO
        )
    )
    clean_graph_store.upsert_relationship(
        GraphRelationship(
            id="rel_D_A", source_id="node_D", target_id="node_A", type=RelationType.REFERS_TO
        )
    )

    # Middle-out traversal from node_B with max_depth=1
    res_depth_1 = clean_graph_store.traverse_middle_out(
        TraversalRequest(anchor_id="node_B", max_depth=1, direction="BOTH")
    )
    # At depth 1, node_B connects to node_A (incoming) and node_C (outgoing)
    connected_ids = {n.id for n in res_depth_1.connected_entities}
    assert "node_A" in connected_ids
    assert "node_C" in connected_ids
    assert "node_D" not in connected_ids

    # Traversal with cycle should terminate cleanly without infinite loop
    res_full = clean_graph_store.traverse_middle_out(
        TraversalRequest(anchor_id="node_B", max_depth=4, direction="BOTH")
    )
    assert res_full.total_nodes == 4  # A, B, C, D

