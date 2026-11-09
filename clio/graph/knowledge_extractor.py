"""Historical Knowledge Graph Extractor with Provenance, Entity Resolution, and Hypothesis Guardrails."""
import hashlib
import re
from typing import Dict, List, Optional, Set, Tuple

from clio.models.graph import (
    GraphNode,
    GraphRelationship,
    NodeType,
    RelationType,
    VerificationStatus,
)
from clio.storage.graph_store import graph_store
from clio.storage.vector_store import vector_store

# Entity Canonical Dictionary with Historical Aliases
CANONICAL_ENTITIES = {
    # Persons
    "person_kumudendu_muni": {
        "type": NodeType.PERSON,
        "name": "Kumudendu Muni",
        "aliases": ["kumudendu", "kumudendu muni", "kumudendracharya", "ಕುಮುದೇಂದು", "ಕುಮುದೇಂದು ಮುನಿ", "ಕುಮುದೇಂದ್ರಾಚಾರ್ಯ"],
        "properties": {"role": "Jain Acharya & Poet", "era": "c. 800-850 CE", "tradition": "Digambara"},
    },
    "person_dharasena": {
        "type": NodeType.PERSON,
        "name": "Acharya Dharasena",
        "aliases": ["dharasena", "dharasenacharya", "ಧಾರಸೇನ", "ಧಾರಸೇನಾಚಾರ್ಯ"],
        "properties": {"role": "Shatkhandagama Teacher", "tradition": "Digambara"},
    },
    "person_yellappa_shastri": {
        "type": NodeType.PERSON,
        "name": "Yellappa Shastri",
        "aliases": ["yellappa shastri", "k. yellappa shastri", "ಯಲ್ಲಪ್ಪ ಶಾಸ್ತ್ರಿ"],
        "properties": {"role": "20th Century Manuscript Decipherment Pioneer", "era": "1953 CE"},
    },
    # Works
    "work_siri_bhoovalaya": {
        "type": NodeType.WORK,
        "name": "Siri Bhoovalaya",
        "aliases": ["siri bhoovalaya", "siri bhuvalaya", "siribhoovalaya", "ಸಿರಿಭೂವಲಯ", "ಸಿರಿ ಭೂವಲಯ"],
        "properties": {"script": "Kannada Numerals", "language": "Multilingual via Kannada", "structure": "Chakra Matrices"},
    },
    "work_shatkhandagama": {
        "type": NodeType.WORK,
        "name": "Shatkhandagama",
        "aliases": ["shatkhandagama", "ಷಟ್ಖಂಡಾಗಮ"],
        "properties": {"language": "Prakrit", "genre": "Canonical Scripture"},
    },
    # Concepts
    "concept_bandha": {
        "type": NodeType.CONCEPT,
        "name": "Bandha",
        "aliases": ["bandha", "bandhas", "ಬಂಧ"],
        "properties": {"description": "Chitra-Kavya geometric traversal pattern"},
    },
    "concept_sarvatobhadra": {
        "type": NodeType.CONCEPT,
        "name": "Sarvatobhadra Bandha",
        "aliases": ["sarvatobhadra", "sarvatobhadra bandha", "ಸರ್ವತೋಭದ್ರ"],
        "properties": {"geometry": "Omnidirectional 360-degree matrix traversal"},
    },
    "concept_ankaphala": {
        "type": NodeType.CONCEPT,
        "name": "Ankaphala",
        "aliases": ["ankaphala", "ankakavya", "ಅಂಕಫಲ"],
        "properties": {"description": "Numerical to phonemic encoding table (1-64)"},
    },
    # Languages
    "lang_halegannada": {
        "type": NodeType.LANGUAGE,
        "name": "Halegannada",
        "aliases": ["halegannada", "old kannada", "ಹಳೆಗನ್ನಡ", "ಪೂರ್ವದ ಹಳೆಗನ್ನಡ"],
        "properties": {"family": "Dravidian", "status": "Classical Historical Stage"},
    },
    "lang_prakrit": {
        "type": NodeType.LANGUAGE,
        "name": "Prakrit",
        "aliases": ["prakrit", "shauraseni", "ardhamagadhi", "ಪ್ರಾಕೃತ"],
        "properties": {"family": "Indo-Aryan", "status": "Middle Indo-Aryan"},
    },
    "lang_sanskrit": {
        "type": NodeType.LANGUAGE,
        "name": "Sanskrit",
        "aliases": ["sanskrit", "ಸಂಸ್ಕೃತ"],
        "properties": {"family": "Indo-Aryan", "status": "Classical"},
    },
}


class KnowledgeGraphExtractor:
    """Extracts provenance-grounded knowledge graph entities and relationships."""

    def __init__(self):
        self._init_canonical_ontology()

    def _init_canonical_ontology(self) -> None:
        """Seed canonical entities into the graph store idempotently."""
        for eid, edata in CANONICAL_ENTITIES.items():
            node = GraphNode(
                id=eid,
                type=edata["type"],
                name=edata["name"],
                properties=edata.get("properties", {}),
                verification_status=VerificationStatus.VERIFIED,
                source_reference="Historical Scholarly Canon",
            )
            graph_store.upsert_node(node)

    def resolve_entity(self, text_mention: str) -> Optional[Tuple[str, NodeType]]:
        """Resolve a textual surface mention to a canonical entity ID and type."""
        normalized = text_mention.strip().lower()
        for eid, edata in CANONICAL_ENTITIES.items():
            for alias in edata["aliases"]:
                if alias in normalized:
                    return eid, edata["type"]
        return None

    def segment_passages(
        self, text: str, page_number: int, document_id: str
    ) -> List[Tuple[str, str]]:
        """Segment raw text into passages and return (passage_id, passage_text)."""
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30]
        if not paragraphs:
            paragraphs = [p.strip() for p in text.split("\n") if len(p.strip()) > 30]

        passages = []
        for idx, para in enumerate(paragraphs, start=1):
            passage_id = f"passage_{document_id}_p{page_number:03d}_{idx:02d}"
            passages.append((passage_id, para))
        return passages

    def extract_from_page(
        self,
        document_id: str,
        page_id: str,
        page_number: int,
        raw_text: str,
        classification: str,
    ) -> List[GraphNode]:
        """Extract graph entities and relationships with provenance from a processed page."""
        new_nodes: List[GraphNode] = []

        # 1. Page node
        page_node = GraphNode(
            id=page_id,
            type=NodeType.PAGE,
            name=f"Page {page_number}",
            properties={"page_number": page_number, "classification": classification},
            source_reference=f"{document_id}#page={page_number}",
            verification_status=VerificationStatus.VERIFIED,
        )
        graph_store.upsert_node(page_node)
        new_nodes.append(page_node)

        # Link Document -> Page
        doc_node = graph_store.get_node(document_id)
        if doc_node:
            rel = GraphRelationship(
                id=f"rel_{document_id}_page_{page_id}",
                source_id=document_id,
                target_id=page_id,
                type=RelationType.CONTAINS_PAGE,
                confidence=1.0,
                verification_status=VerificationStatus.VERIFIED,
                source_document_id=document_id,
                source_page_number=page_number,
            )
            graph_store.upsert_relationship(rel)

        if not raw_text:
            return new_nodes

        # 2. Segment passages
        passages = self.segment_passages(raw_text, page_number, document_id)
        for passage_id, passage_text in passages:
            # Upsert Passage node
            p_node = GraphNode(
                id=passage_id,
                type=NodeType.PASSAGE,
                name=f"Passage {passage_id}",
                properties={"text": passage_text[:200], "char_length": len(passage_text)},
                source_reference=f"{document_id}#page={page_number}",
                verification_status=VerificationStatus.VERIFIED,
            )
            graph_store.upsert_node(p_node)
            new_nodes.append(p_node)

            # Link Page -> HAS_PASSAGE -> Passage
            rel_page_pass = GraphRelationship(
                id=f"rel_{page_id}_{passage_id}",
                source_id=page_id,
                target_id=passage_id,
                type=RelationType.HAS_PASSAGE,
                confidence=1.0,
                verification_status=VerificationStatus.VERIFIED,
                source_document_id=document_id,
                source_page_number=page_number,
            )
            graph_store.upsert_relationship(rel_page_pass)

            # Index passage in Qdrant for semantic search
            vector_store.index_passage(
                passage_id=passage_id,
                text=passage_text,
                document_id=document_id,
                page_number=page_number,
            )

            # 3. Create Evidence node for this passage
            ev_id = f"evidence_{hashlib.sha256(passage_text.encode('utf-8')).hexdigest()[:16]}"
            ev_node = GraphNode(
                id=ev_id,
                type=NodeType.EVIDENCE,
                name=f"Evidence from Page {page_number}",
                properties={"verbatim_excerpt": passage_text[:300]},
                source_reference=f"{document_id}#page={page_number}",
                verification_status=VerificationStatus.VERIFIED,
            )
            graph_store.upsert_node(ev_node)
            new_nodes.append(ev_node)

            # Link Passage -> SUPPORTED_BY -> Evidence
            rel_ev = GraphRelationship(
                id=f"rel_{passage_id}_{ev_id}",
                source_id=passage_id,
                target_id=ev_id,
                type=RelationType.SUPPORTED_BY,
                confidence=1.0,
                verification_status=VerificationStatus.VERIFIED,
                source_document_id=document_id,
                source_page_number=page_number,
                evidence_id=ev_id,
            )
            graph_store.upsert_relationship(rel_ev)

            # 4. Entity Mention Recognition
            matched_entities: Set[str] = set()
            for eid, edata in CANONICAL_ENTITIES.items():
                for alias in edata["aliases"]:
                    if alias in passage_text.lower():
                        matched_entities.add(eid)
                        break

            # Link Passage to matched entities via REFERS_TO or DISCUSSES
            for target_eid in matched_entities:
                rel_ref = GraphRelationship(
                    id=f"rel_{passage_id}_ref_{target_eid}",
                    source_id=passage_id,
                    target_id=target_eid,
                    type=RelationType.REFERS_TO,
                    confidence=0.95,
                    verification_status=VerificationStatus.VERIFIED,
                    source_document_id=document_id,
                    source_page_number=page_number,
                    evidence_id=ev_id,
                )
                graph_store.upsert_relationship(rel_ref)

            # 5. Guardrail against promoting speculative hypotheses to facts:
            # If text discusses unproven or conjectural historical claims (e.g. 718 languages, dates before 800 CE),
            # mark as Hypothesis node with status PROPOSED!
            if "718" in passage_text or "ಹೇಳಿಕೆ" in passage_text or "hypothes" in passage_text.lower():
                hyp_id = f"hyp_{passage_id[:20]}"
                hyp_node = GraphNode(
                    id=hyp_id,
                    type=NodeType.HYPOTHESIS,
                    name=f"Hypothesis on {passage_id}",
                    properties={"claim": passage_text[:200], "status": "Proposed Claim"},
                    source_reference=f"{document_id}#page={page_number}",
                    verification_status=VerificationStatus.PROPOSED,
                )
                graph_store.upsert_node(hyp_node)
                new_nodes.append(hyp_node)

                # Link Hypothesis -> DERIVED_FROM -> Evidence
                rel_hyp = GraphRelationship(
                    id=f"rel_{hyp_id}_derived_{ev_id}",
                    source_id=hyp_id,
                    target_id=ev_id,
                    type=RelationType.DERIVED_FROM,
                    confidence=0.60,
                    verification_status=VerificationStatus.PROPOSED,
                    source_document_id=document_id,
                    source_page_number=page_number,
                    evidence_id=ev_id,
                )
                graph_store.upsert_relationship(rel_hyp)

        return new_nodes


knowledge_extractor = KnowledgeGraphExtractor()

