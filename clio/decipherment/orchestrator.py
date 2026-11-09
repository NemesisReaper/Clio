"""Decipherment Orchestrator: End-to-end reproducible numerical-to-phonetic decipherment pipeline."""
import json
import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from clio.decipherment.alignment.aligner import halegannada_aligner
from clio.decipherment.ankaphala.engine import ankaphala_engine
from clio.decipherment.ankaphala.tables import AnkaphalaVersion
from clio.decipherment.bandhas.selector import bandha_engine
from clio.decipherment.context import context_retriever
from clio.decipherment.explainer import (
    ComprehensiveDeciphermentReport,
    DecodingStatus,
    bilingual_explainer,
)
from clio.models.chakra import ChakraMatrix
from clio.models.decipherment import BandhaPattern, DeciphermentRequest
from clio.models.graph import GraphNode, GraphRelationship, NodeType, RelationType, VerificationStatus
from clio.storage.db import ChakraRecord, SessionLocal, ShlokaRecord
from clio.storage.graph_store import graph_store

logger = logging.getLogger(__name__)


class DeciphermentOrchestrator:
    """Orchestrates the 10-stage Siri Bhoovalaya decipherment pipeline."""

    def __init__(self):
        self.bandha_engine = bandha_engine
        self.ankaphala_engine = ankaphala_engine
        self.aligner = halegannada_aligner
        self.context_retriever = context_retriever
        self.explainer = bilingual_explainer

    async def decipher(
        self,
        request: DeciphermentRequest,
        db: Optional[Session] = None,
        reference_shloka_text: Optional[str] = None,
        table_version: AnkaphalaVersion = AnkaphalaVersion.V1_YELLAPPA_SHASTRI_1953,
    ) -> ComprehensiveDeciphermentReport:
        """Execute the end-to-end reproducible decipherment pipeline."""
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            # 1. Matrix Retrieval
            ch_rec = db.query(ChakraRecord).filter(ChakraRecord.id == request.chakra_id).first()
            if not ch_rec:
                raise ValueError(f"Chakra '{request.chakra_id}' not found in database.")

            matrix_grid = json.loads(ch_rec.matrix_grid_json or "[]")
            matrix = ChakraMatrix(
                chakra_id=ch_rec.id,
                document_id=ch_rec.document_id,
                page_id=ch_rec.page_id,
                chakra_number=ch_rec.chakra_number,
                rows=ch_rec.rows,
                cols=ch_rec.cols,
                expected_cells=ch_rec.expected_cells,
                total_extracted_cells=ch_rec.total_extracted_cells,
                is_valid=ch_rec.is_valid,
                matrix_grid=matrix_grid,
                validation_errors=json.loads(ch_rec.validation_errors_json or "[]"),
            )

            # 2. Bandha Selection & Compatibility Validation
            if not self.bandha_engine.validate_bandha_compatibility(matrix, request.selected_bandha):
                raise ValueError(
                    f"Chakra '{request.chakra_id}' does not satisfy geometric preconditions for {request.selected_bandha}"
                )

            # 3. Coordinate Traversal Generation
            trajectory = self.bandha_engine.generate_trajectory(
                bandha=request.selected_bandha,
                start_coord=request.start_coordinate,
                max_steps=729,
                params=request.custom_parameters,
            )

            # 4. Numerical Stream Extraction (Strictly zero silent infill)
            numerical_stream = self.bandha_engine.extract_numerical_stream(matrix, trajectory)

            # 5. Ankaphala Substitution: Raw (Tier 1) and Composed (Tier 2)
            raw_tokens = self.ankaphala_engine.substitute_raw(numerical_stream)
            decoded_phonetics = self.ankaphala_engine.substitute(
                numerical_stream, version=table_version
            )

            # 6. Reference Shloka Lookup
            ref_text = reference_shloka_text
            if not ref_text:
                # Look up associated shloka from database for this document/page
                shloka_rec = (
                    db.query(ShlokaRecord)
                    .filter(
                        (ShlokaRecord.chakra_id == request.chakra_id)
                        | (ShlokaRecord.page_id == ch_rec.page_id)
                    )
                    .first()
                )
                if shloka_rec:
                    ref_text = shloka_rec.normalized_unicode or shloka_rec.raw_text

            # 7. Shloka Alignment
            alignment = None
            if ref_text:
                alignment = self.aligner.align(
                    candidate_text=decoded_phonetics,
                    reference_shloka_text=ref_text,
                )

            # 8. Historical Context Retrieval
            graph_context = await self.context_retriever.retrieve_context(
                verse_text=ref_text or decoded_phonetics,
                anchor_id="work_siri_bhoovalaya",
                max_depth=2,
            )

            # 9. Bilingual Explanation Generation with 5-Tier Output Separation
            matrix_comp = (
                matrix.total_extracted_cells / 729.0
                if matrix.total_extracted_cells and matrix.total_extracted_cells > 0
                else 1.0
            )
            report = self.explainer.generate_report(
                chakra_id=request.chakra_id,
                bandha_name=request.selected_bandha.value,
                table_version=table_version.value,
                decoded_phonetics=decoded_phonetics,
                reference_shloka=ref_text,
                alignment=alignment,
                graph_context=graph_context,
                direct_extracted_tokens=raw_tokens,
                matrix_completeness=matrix_comp,
            )

            # 10. Store Evidence and Provenance in Knowledge Graph
            self._persist_decipherment_evidence(report, matrix, trajectory, numerical_stream)

            return report

        finally:
            if should_close:
                db.close()

    def _persist_decipherment_evidence(
        self,
        report: ComprehensiveDeciphermentReport,
        matrix: ChakraMatrix,
        trajectory,
        numerical_stream: List[int],
    ) -> None:
        """Record decipherment run as an immutable Evidence and Hypothesis node in the graph."""
        try:
            ev_id = f"evidence_decipher_{matrix.chakra_id}_{report.bandha_name.lower()}"
            ev_node = GraphNode(
                id=ev_id,
                type=NodeType.EVIDENCE,
                name=f"Decipherment Evidence for {matrix.chakra_id}",
                properties={
                    "chakra_id": matrix.chakra_id,
                    "bandha": report.bandha_name,
                    "table_version": report.table_version,
                    "confidence_score": report.confidence_score,
                    "decoding_status": report.decoding_status.value,
                    "numerical_sample": str(numerical_stream[:16]),
                    "phonetic_sample": report.decoded_phonetic_sequence[:64],
                },
                source_reference=f"Chakra:{matrix.chakra_id}#Bandha:{report.bandha_name}",
                verification_status=(
                    VerificationStatus.VERIFIED
                    if report.decoding_status == DecodingStatus.VERIFIED_DECODING
                    else VerificationStatus.PROPOSED
                ),
            )
            graph_store.upsert_node(ev_node)

            # If candidate or proposed decoding, create Hypothesis node linked via DERIVED_FROM
            if report.decoding_status != DecodingStatus.VERIFIED_DECODING:
                hyp_id = f"hyp_decipher_{matrix.chakra_id}_{report.bandha_name.lower()}"
                hyp_node = GraphNode(
                    id=hyp_id,
                    type=NodeType.HYPOTHESIS,
                    name=f"Decipherment Candidate: {report.bandha_name} on {matrix.chakra_id}",
                    properties={
                        "hypothesis_statement": f"Decoded text candidate: {report.cleaned_segmented_verse[:100]}",
                        "status": "Candidate Decipherment",
                    },
                    source_reference=f"Chakra:{matrix.chakra_id}",
                    verification_status=VerificationStatus.PROPOSED,
                )
                graph_store.upsert_node(hyp_node)

                rel = GraphRelationship(
                    id=f"rel_{hyp_id}_derived_{ev_id}",
                    source_id=hyp_id,
                    target_id=ev_id,
                    type=RelationType.DERIVED_FROM,
                    confidence=report.confidence_score,
                    verification_status=VerificationStatus.PROPOSED,
                )
                graph_store.upsert_relationship(rel)

        except Exception as e:
            logger.error("Failed to persist decipherment evidence to graph: %s", e)


decipherment_orchestrator = DeciphermentOrchestrator()

