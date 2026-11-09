"""Day 3 Historical Validation, Source Provenance, and Real-Data Integration Tests.

Audits:
- Incorrect or missing provenance
- Unverified and experimental Bandha rules
- Raw vs normalized Ankaphala tables and archaic character preservation
- Incomplete matrices and refusal of silent infill
- False-positive alignment detection
- Unicode normalization preserving verbatim raw text
- Uncertain Chakra-shloka associations (guardrail against score-based auto-association)
- Decipherment reproducibility
- Multi-dimensional confidence decoupling
- Real-data availability inspection without manufacturing evidence
"""
import random
import unicodedata
import pytest
from fastapi.testclient import TestClient

from clio.api.app import app
from clio.decipherment.alignment.aligner import halegannada_aligner
from clio.decipherment.ankaphala.engine import ankaphala_engine
from clio.decipherment.ankaphala.tables import (
    RAW_HISTORICAL_ANKAPHALA_V1,
    TABLE_V1_PROVENANCE_AUDIT,
    AnkaphalaVersion,
)
from clio.decipherment.bandhas.base import TraversalDirection
from clio.decipherment.bandhas.selector import bandha_engine
from clio.decipherment.historical_reference import (
    HISTORICAL_CHAKRA1_NUMERICAL_SEQUENCE,
    HISTORICAL_MANGALACHARANA_SHLOKA,
    HISTORICAL_REFERENCE_PROVENANCE,
    generate_historical_chakra1_grid,
)
from clio.decipherment.orchestrator import decipherment_orchestrator
from clio.decipherment.provenance.registry import provenance_registry
from clio.models.chakra import ChakraMatrix
from clio.models.decipherment import BandhaPattern, DeciphermentRequest
from clio.models.provenance import (
    DocumentationLevel,
    RuleVerificationState,
)
from clio.storage.db import ChakraRecord, DocumentRecord, PageRecord, ShlokaRecord
from clio.validation.engine import historical_validation_engine


client = TestClient(app)


def test_missing_or_unregistered_provenance_flagged():
    """Unregistered rule queries must return UNVERIFIED state and fail formal validation."""
    state = provenance_registry.get_rule_verification_state("RULE_NON_EXISTENT_FAKE_BANDHA")
    assert state == RuleVerificationState.UNVERIFIED

    result = historical_validation_engine.run_validation(
        target_type="RULE",
        target_id="RULE_NON_EXISTENT_FAKE_BANDHA",
    )
    assert not result.is_valid
    assert result.verification_state == RuleVerificationState.UNVERIFIED
    assert len(result.errors) > 0
    assert "not registered" in result.errors[0]


def test_unverified_and_experimental_bandha_rules():
    """Bandha algorithms must separate verified poetics concepts from experimental trajectories."""
    sarv = bandha_engine.get_bandha(BandhaPattern.SARVATOBHADRA)
    assert sarv.metadata.verification_state == RuleVerificationState.PARTIALLY_VERIFIED
    assert "100% coverage does not prove" in sarv.metadata.authenticity_disclaimer

    # Serpentine raster is purely experimental
    serp_rule = provenance_registry.get_rule_provenance("RULE_BANDHA_SARVATOBHADRA_SERPENTINE")
    assert serp_rule is not None
    assert serp_rule.verification_state == RuleVerificationState.EXPERIMENTAL
    assert serp_rule.documentation_level == DocumentationLevel.EXPERIMENTAL

    # Padmabandha 8-petal is partially verified (concept classical, 27x27 discretization inferred)
    padma = bandha_engine.get_bandha(BandhaPattern.PADMABANDHA)
    assert padma.metadata.verification_state == RuleVerificationState.PARTIALLY_VERIFIED
    assert padma.metadata.documentation_level == DocumentationLevel.INFERRED


def test_ankaphala_raw_table_independence_and_archaic_preservation():
    """Raw 1953 Ankaphala table must be stored independently from normalized representations."""
    raw_table = ankaphala_engine.get_raw_table()
    assert len(raw_table) == 64

    # Verify archaic Halegannada phonemes in raw table
    assert raw_table[51].raw_grapheme == "ಱ"
    assert raw_table[51].is_archaic is True
    assert raw_table[52].raw_grapheme == "ೞ"
    assert raw_table[52].is_archaic is True

    # Test substitute_raw: must NOT apply vowel ligature composition
    # E.g. [17 (ಕ), 2 (ಆ)] -> ['ಕ', 'ಆ'], NOT 'ಕಾ'
    raw_sub = ankaphala_engine.substitute_raw([17, 2, 51, 52])
    assert raw_sub == ["ಕ", "ಆ", "ಱ", "ೞ"]

    # In contrast, substitute() applies algorithmic composition (Tier 2)
    composed_sub = ankaphala_engine.substitute([17, 2, 51, 52])
    assert composed_sub == "ಕಾಱೞ"

    # Audit provenance must be PARTIALLY_VERIFIED
    prov = ankaphala_engine.get_table_provenance()
    assert prov.verification_state == RuleVerificationState.PARTIALLY_VERIFIED
    assert prov.total_symbols == 64


def test_missing_matrix_cells_refuses_silent_infill():
    """Incomplete matrices must report missing cells and refuse silent infill."""
    grid = [[1 for _ in range(27)] for _ in range(27)]
    grid[0][0] = None  # Missing cell at top-left
    grid[13][13] = None  # Missing cell at center
    grid[5][5] = 99  # Out of domain value

    audit = historical_validation_engine.audit_matrix_dataset(
        matrix_grid=grid,
        document_id="doc_synthetic_test_audit",
        chakra_number=999,
    )
    assert audit["is_valid"] is False
    assert audit["missing_cells_count"] == 2
    assert audit["out_of_domain_cells_count"] == 1
    assert audit["verification_state"] == RuleVerificationState.UNVERIFIED

    # Check that BandhaEngine.extract_numerical_stream raises ValueError
    matrix_model = ChakraMatrix(
        chakra_id="chk_missing_test",
        document_id="doc_test",
        page_id="page_test",
        rows=27,
        cols=27,
        expected_cells=729,
        total_extracted_cells=727,
        is_valid=False,
        matrix_grid=grid,
    )
    traj = bandha_engine.generate_trajectory(BandhaPattern.SARVATOBHADRA)
    with pytest.raises(ValueError, match="Cannot silently fill missing cells"):
        bandha_engine.extract_numerical_stream(matrix_model, traj)


def test_false_positive_alignment_detection():
    """Random / nonsensical syllables aligned against historical shloka must yield low similarity."""
    # Synthetic random noise
    random_noise = "ಟಥಡಢಣತಥದಧನಯರವಲಶಷಸಹಳಙಞ"
    report = halegannada_aligner.align(
        candidate_text=random_noise,
        reference_shloka_text=HISTORICAL_MANGALACHARANA_SHLOKA,
    )
    assert report.is_verified_match is False
    assert report.similarity_score < 0.35
    assert report.mismatches > 10


def test_unicode_normalization_preserves_verbatim_text():
    """Reference shloka audit must preserve raw verbatim text separately from NFC normalization."""
    raw_sample = "ಶ್ರೀಮತ್ಪರಮ\u0020ಗಂಭೀರ\u0020ಸ್ಯಾದ್ವಾದಾಮೋಘ\u0020ಲಾಂಛನಂ\u0020||"
    audit = historical_validation_engine.audit_reference_shloka(
        raw_text=raw_sample,
        source_citation="Yellappa Shastri 1953, p. 28",
        associated_chakra_id="chakra_1",
        is_association_explicit=True,
    )
    assert audit["verbatim_raw_text"] == raw_sample
    assert audit["normalized_unicode"] == unicodedata.normalize("NFC", raw_sample)
    assert audit["is_association_explicit_in_source"] is True
    assert audit["is_association_uncertain"] is False


def test_uncertain_chakra_shloka_association_guardrails():
    """Shloka without explicit primary text association must be flagged as uncertain."""
    audit = historical_validation_engine.audit_reference_shloka(
        raw_text="ಜಯತಿ ಭಗವಾನ್ ಜಿನೇಂದ್ರಃ ||",
        source_citation="Unspecified palm-leaf folio fragment",
        associated_chakra_id="chakra_42",
        is_association_explicit=False,  # Not explicitly attested in primary text
    )
    assert audit["is_association_explicit_in_source"] is False
    assert audit["is_association_uncertain"] is True
    assert "Uncertain Association" in audit["non_association_warning"]


def test_decipherment_reproducibility_across_runs(test_db):
    """Running decipherment twice with identical parameters must produce bit-for-bit identical results."""
    # Seed historical Chakra 1 in DB
    grid = generate_historical_chakra1_grid()
    doc = DocumentRecord(
        id="doc_audit_repro",
        filename="manuscript_chakra1_audit.pdf",
        sha256_hash="hash_repro_audit_12345",
        file_size_bytes=1024,
        storage_path="/data/audit.pdf",
    )
    page = PageRecord(id="page_audit_repro", document_id=doc.id, page_number=1)
    chakra = ChakraRecord(
        id="chakra_audit_repro",
        document_id=doc.id,
        page_id=page.id,
        chakra_number=1,
        rows=27,
        cols=27,
        expected_cells=729,
        total_extracted_cells=729,
        is_valid=True,
        matrix_grid_json=str(grid),
    )
    test_db.add_all([doc, page, chakra])
    test_db.commit()

    import asyncio
    req = DeciphermentRequest(
        chakra_id="chakra_audit_repro",
        selected_bandha=BandhaPattern.SARVATOBHADRA,
    )

    run1 = asyncio.run(
        decipherment_orchestrator.decipher(
            request=req,
            db=test_db,
            reference_shloka_text=HISTORICAL_MANGALACHARANA_SHLOKA,
        )
    )
    run2 = asyncio.run(
        decipherment_orchestrator.decipher(
            request=req,
            db=test_db,
            reference_shloka_text=HISTORICAL_MANGALACHARANA_SHLOKA,
        )
    )

    assert run1.decoded_phonetic_sequence == run2.decoded_phonetic_sequence
    assert run1.confidence_score == run2.confidence_score
    assert run1.directly_extracted_tokens == run2.directly_extracted_tokens
    assert len(run1.directly_extracted_tokens) == 729


def test_real_data_status_reports_pending_without_manufacturing_data(test_db):
    """System must report PENDING_PRIMARY_SOURCE_DEPOSIT when only synthetic fixtures exist."""
    status = historical_validation_engine.inspect_real_data_availability(db=test_db)
    assert status["real_data_available"] is False
    assert status["status"] == "PENDING_PRIMARY_SOURCE_DEPOSIT"
    assert "Real-data validation remains pending" in status["message"]


def test_decipherment_confidence_breakdown_decoupling():
    """Confidence reporting must decouple matrix completeness, rule verification, and alignment."""
    from clio.decipherment.explainer import bilingual_explainer
    report = bilingual_explainer.generate_report(
        chakra_id="chakra_sample",
        bandha_name="SARVATOBHADRA",
        table_version="v1_yellappa_shastri_1953",
        decoded_phonetics="ಶ್ರೀಮತ್ಪರಮ ಗಂಭೀರ",
        reference_shloka=HISTORICAL_MANGALACHARANA_SHLOKA,
        alignment=None,
        graph_context=None,
        direct_extracted_tokens=["ಶ್ರೀ", "ಮ", "ತ"],
        matrix_completeness=1.0,
    )
    assert report.detailed_confidence_breakdown is not None
    bd = report.detailed_confidence_breakdown
    assert bd.matrix_extraction_completeness == 1.0
    assert bd.bandha_rule_verification == RuleVerificationState.PARTIALLY_VERIFIED
    assert bd.ankaphala_table_verification == RuleVerificationState.PARTIALLY_VERIFIED
    assert bd.traversal_reproducibility == 1.0
    assert bd.is_calibrated_heuristic is True
    assert report.is_authoritative_claim is False
    assert len(report.directly_extracted_tokens) == 3


def test_provenance_and_validation_api_endpoints():
    """Test REST API endpoints for rules, provenance, sources, and validation."""
    # 1. GET /api/v1/decipher/rules
    res_rules = client.get("/api/v1/decipher/rules")
    assert res_rules.status_code == 200
    rules = res_rules.json()
    assert len(rules) >= 6
    rule_ids = [r["rule_id"] for r in rules]
    assert "RULE_BANDHA_SARVATOBHADRA_CONCENTRIC_SPIRAL" in rule_ids
    assert "RULE_ANKAPHALA_TABLE_V1_1953" in rule_ids

    # 2. GET /api/v1/decipher/rules/{rule_id}/provenance
    res_single = client.get("/api/v1/decipher/rules/RULE_BANDHA_SARVATOBHADRA_CONCENTRIC_SPIRAL/provenance")
    assert res_single.status_code == 200
    data = res_single.json()
    assert data["rule_id"] == "RULE_BANDHA_SARVATOBHADRA_CONCENTRIC_SPIRAL"
    assert data["verification_state"] == "PARTIALLY_VERIFIED"
    assert "Dandin" in data["exact_citation"]

    # 3. GET /api/v1/sources
    res_sources = client.get("/api/v1/sources")
    assert res_sources.status_code == 200
    sources = res_sources.json()
    assert len(sources) >= 4
    source_ids = [s["id"] for s in sources]
    assert "src_yellappa_shastri_1953" in source_ids
    assert "src_kavyadarsha_dandin" in source_ids

    # 4. GET /api/v1/validation/real-data-status
    res_rd = client.get("/api/v1/validation/real-data-status")
    assert res_rd.status_code == 200
    rd_data = res_rd.json()
    assert "status" in rd_data

    # 5. POST /api/v1/validation/run
    val_payload = {
        "target_type": "RULE",
        "target_id": "RULE_ANKAPHALA_TABLE_V1_1953",
    }
    res_val = client.post("/api/v1/validation/run", json=val_payload)
    assert res_val.status_code == 200
    val_data = res_val.json()
    assert val_data["is_valid"] is True
    assert val_data["verification_state"] == "PARTIALLY_VERIFIED"
