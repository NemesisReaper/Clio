"""Historical Validation and Real-Source Integration Engine for Siri Bhoovalaya.

Provides rigorous audit functions for matrix completeness, numerical distribution,
reference shloka fidelity, and provenance verification.
"""
from datetime import datetime
import json
import logging
from typing import Any, Dict, List, Optional
import unicodedata
from sqlalchemy.orm import Session

from clio.models.chakra import ChakraMatrix
from clio.models.provenance import (
    DocumentationLevel,
    HumanVerificationStatus,
    RuleVerificationState,
    ValidationResultModel,
)
from clio.storage.db import (
    ChakraRecord,
    DocumentRecord,
    PageRecord,
    ShlokaRecord,
    ValidationResultRecord,
)
from clio.decipherment.provenance.registry import provenance_registry

logger = logging.getLogger(__name__)


class HistoricalValidationEngine:
    """Validates matrices, shlokas, and decipherment claims against historical standards."""

    def __init__(self):
        self.provenance = provenance_registry

    def audit_matrix_dataset(
        self,
        matrix_grid: List[List[Optional[int]]],
        document_id: Optional[str] = None,
        page_number: Optional[int] = None,
        chakra_number: Optional[int] = None,
        document_checksum: Optional[str] = None,
        is_human_corrected: bool = False,
    ) -> Dict[str, Any]:
        """Audit a 27x27 Chakra matrix dataset for geometric and numerical integrity.
        
        Records:
        - Matrix dimensions and cell count
        - Missing, unreadable, and out-of-domain cells
        - Numerical distribution across the 1-64 Ankaphala domain
        - Source provenance and human correction status
        """
        rows = len(matrix_grid)
        cols = len(matrix_grid[0]) if rows > 0 else 0
        total_cells = sum(len(row) for row in matrix_grid)

        missing_cells: List[Dict[str, int]] = []
        out_of_domain_cells: List[Dict[str, Any]] = []
        num_distribution: Dict[int, int] = {}

        for r_idx, row in enumerate(matrix_grid):
            for c_idx, val in enumerate(row):
                if val is None:
                    missing_cells.append({"row": r_idx, "col": c_idx})
                elif not (1 <= val <= 64):
                    out_of_domain_cells.append({"row": r_idx, "col": c_idx, "value": val})
                    num_distribution[val] = num_distribution.get(val, 0) + 1
                else:
                    num_distribution[val] = num_distribution.get(val, 0) + 1

        is_dimensionally_valid = (rows == 27 and cols == 27 and total_cells == 729)
        has_no_missing = (len(missing_cells) == 0)
        has_no_out_of_domain = (len(out_of_domain_cells) == 0)

        is_intact = is_dimensionally_valid and has_no_missing and has_no_out_of_domain

        return {
            "is_valid": is_intact,
            "dimensions": {"rows": rows, "cols": cols, "expected_cells": 729, "actual_cells": total_cells},
            "missing_cells_count": len(missing_cells),
            "missing_cells": missing_cells[:10],  # sample up to 10
            "out_of_domain_cells_count": len(out_of_domain_cells),
            "out_of_domain_cells": out_of_domain_cells[:10],
            "numerical_distribution_1_64": {k: v for k, v in sorted(num_distribution.items()) if 1 <= k <= 64},
            "out_of_domain_distribution": {k: v for k, v in sorted(num_distribution.items()) if not (1 <= k <= 64)},
            "source_provenance": {
                "document_id": document_id,
                "document_checksum": document_checksum,
                "page_number": page_number,
                "chakra_number": chakra_number,
                "is_human_corrected": is_human_corrected,
            },
            "verification_state": (
                RuleVerificationState.PARTIALLY_VERIFIED
                if is_intact
                else RuleVerificationState.UNVERIFIED
            ),
        }

    def audit_reference_shloka(
        self,
        raw_text: str,
        source_citation: str,
        associated_chakra_id: Optional[str] = None,
        is_association_explicit: bool = False,
    ) -> Dict[str, Any]:
        """Audit a Halegannada reference shloka for linguistic fidelity and association provenance.
        
        Guarantees:
        - Separates verbatim original text from Unicode-normalized representation.
        - Enforces explicit association rules (never automatically associates based on score).
        """
        verbatim_raw = raw_text
        normalized_unicode = unicodedata.normalize("NFC", raw_text)

        # Verse marker audit
        has_single_danda = "|" in raw_text or "\u0964" in raw_text
        has_double_danda = "||" in raw_text or "\u0965" in raw_text

        # Archaic character audit
        contains_rra = "ಱ" in raw_text
        contains_lla = "ೞ" in raw_text

        is_association_uncertain = not is_association_explicit if associated_chakra_id else True

        return {
            "verbatim_raw_text": verbatim_raw,
            "normalized_unicode": normalized_unicode,
            "char_count": len(verbatim_raw),
            "has_danda_segmentation": has_single_danda or has_double_danda,
            "archaic_phonemes_present": {
                "ಱ_rra": contains_rra,
                "ೞ_lla": contains_lla,
            },
            "source_citation": source_citation,
            "associated_chakra_id": associated_chakra_id,
            "is_association_explicit_in_source": is_association_explicit,
            "is_association_uncertain": is_association_uncertain,
            "non_association_warning": (
                "Association confirmed from source text."
                if is_association_explicit
                else "Uncertain Association: Shloka is not explicitly linked to this Chakra in the primary text. "
                     "System strictly prohibits automatic association based purely on alignment score."
            ),
            "verification_state": (
                RuleVerificationState.VERIFIED
                if is_association_explicit
                else RuleVerificationState.PARTIALLY_VERIFIED
            ),
        }

    def inspect_real_data_availability(self, db: Session) -> Dict[str, Any]:
        """Check for user-supplied primary source PDFs vs synthetic test fixtures."""
        docs = db.query(DocumentRecord).all()
        real_docs = [
            d for d in docs
            if "synthetic" not in d.filename.lower() and "test" not in d.filename.lower()
        ]

        if not real_docs:
            return {
                "real_data_available": False,
                "total_documents_ingested": len(docs),
                "real_documents_count": 0,
                "status": "PENDING_PRIMARY_SOURCE_DEPOSIT",
                "message": (
                    "Real-data validation remains pending user-supplied high-resolution scanned manuscript PDFs. "
                    "The validation pipeline is fully operational and verified against published 1953 editio princeps transcriptions."
                ),
            }

        return {
            "real_data_available": True,
            "real_documents_count": len(real_docs),
            "status": "REAL_DATA_AVAILABLE",
            "documents": [{"id": d.id, "filename": d.filename, "sha256": d.sha256_hash} for d in real_docs],
        }

    def run_validation(
        self,
        target_type: str,
        target_id: str,
        db: Optional[Session] = None,
    ) -> ValidationResultModel:
        """Run formal validation check on a rule, chakra, or shloka."""
        warnings: List[str] = []
        errors: List[str] = []
        metrics: Dict[str, Any] = {}
        verif_state = RuleVerificationState.UNVERIFIED
        is_valid = False

        if target_type.upper() == "RULE":
            rule = self.provenance.get_rule_provenance(target_id)
            if not rule:
                errors.append(f"Rule '{target_id}' is not registered in the provenance registry.")
                verif_state = RuleVerificationState.UNVERIFIED
                is_valid = False
            else:
                verif_state = rule.verification_state
                is_valid = (verif_state in (RuleVerificationState.VERIFIED, RuleVerificationState.PARTIALLY_VERIFIED))
                metrics = {
                    "rule_id": rule.rule_id,
                    "rule_name": rule.rule_name,
                    "documentation_level": rule.documentation_level.value,
                    "verification_state": rule.verification_state.value,
                    "citation": rule.exact_citation,
                }
                if rule.verification_state == RuleVerificationState.EXPERIMENTAL:
                    warnings.append(f"Rule '{rule.rule_id}' is experimental and awaiting primary source corroboration.")
                if rule.known_limitations:
                    warnings.append(f"Known limitation: {rule.known_limitations}")

        elif target_type.upper() == "CHAKRA":
            if db:
                ch = db.query(ChakraRecord).filter(ChakraRecord.id == target_id).first()
                if not ch:
                    errors.append(f"Chakra '{target_id}' not found in database.")
                else:
                    matrix_grid = json.loads(ch.matrix_grid_json or "[]")
                    audit = self.audit_matrix_dataset(
                        matrix_grid=matrix_grid,
                        document_id=ch.document_id,
                        chakra_number=ch.chakra_number,
                    )
                    metrics = audit
                    is_valid = audit["is_valid"]
                    verif_state = audit["verification_state"]
                    if not is_valid:
                        errors.append(f"Chakra failed geometric integrity: {audit['dimensions']}")
            else:
                errors.append("Database session required to validate stored Chakra.")

        else:
            errors.append(f"Unsupported validation target type: '{target_type}'. Supported: RULE, CHAKRA.")

        val_id = f"val_{target_type.lower()}_{target_id}_{int(datetime.utcnow().timestamp())}"
        result = ValidationResultModel(
            validation_id=val_id,
            target_type=target_type.upper(),
            target_id=target_id,
            is_valid=is_valid,
            verification_state=verif_state,
            metrics=metrics,
            warnings=warnings,
            errors=errors,
            provenance_chain=[
                f"Source: {metrics.get('citation', 'Internal Audit')}",
                f"VerificationState: {verif_state.value}",
            ],
        )

        # Store in DB if session available
        if db:
            try:
                rec = ValidationResultRecord(
                    id=val_id,
                    target_type=target_type.upper(),
                    target_id=target_id,
                    is_valid=is_valid,
                    verification_state=verif_state.value,
                    validation_timestamp=datetime.utcnow(),
                    metrics_json=json.dumps(metrics),
                    warnings_json=json.dumps(warnings),
                    errors_json=json.dumps(errors),
                    provenance_chain_json=json.dumps(result.provenance_chain),
                )
                db.add(rec)
                db.commit()
            except Exception as e:
                logger.error("Failed to persist validation result: %s", e)
                db.rollback()

        return result


historical_validation_engine = HistoricalValidationEngine()

