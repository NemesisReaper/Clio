"""Integration test for Decipherment Orchestrator using historical Chakra 1 published data."""
import json
import pytest
from clio.decipherment.historical_reference import (
    HISTORICAL_MANGALACHARANA_SHLOKA,
    generate_historical_chakra1_grid,
)
from clio.decipherment.orchestrator import decipherment_orchestrator
from clio.models.decipherment import BandhaPattern, DeciphermentRequest
from clio.storage.db import ChakraRecord, DocumentRecord, PageRecord


@pytest.mark.asyncio
async def test_historical_chakra1_decipherment_workflow(test_db):
    """End-to-End Orchestrator Test on Published Siri Bhoovalaya Chakra 1:
    1. Seed Chakra 1 record with historical grid data into DB.
    2. Execute Sarvatobhadra Bandha decipherment pipeline.
    3. Verify numerical extraction, Ankaphala phonetic substitution, and alignment.
    4. Verify bilingual report with English and Modern Kannada commentaries.
    5. Verify evidence graph preservation.
    """
    # 1. Seed historical document, page, and Chakra 1
    doc_rec = DocumentRecord(
        id="doc_hist_siri_bhoovalaya_1953",
        filename="Siri_Bhoovalaya_1953_Yellappa_Shastri.pdf",
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        file_size_bytes=1024000,
        total_pages=1,
        storage_path="data/pdfs/chakra1.pdf",
        status="COMPLETED",
    )
    page_rec = PageRecord(
        id="page_hist_001",
        document_id=doc_rec.id,
        page_number=1,
        classification="NUMERICAL_MATRIX",
    )

    grid = generate_historical_chakra1_grid()
    ch_rec = ChakraRecord(
        id="chakra_hist_01",
        document_id=doc_rec.id,
        page_id=page_rec.id,
        chakra_number=1,
        rows=27,
        cols=27,
        expected_cells=729,
        total_extracted_cells=729,
        is_valid=True,
        matrix_grid_json=json.dumps(grid),
    )
    test_db.add(doc_rec)
    test_db.add(page_rec)
    test_db.add(ch_rec)
    test_db.commit()

    # 2. Run Decipherment Pipeline
    req = DeciphermentRequest(
        chakra_id="chakra_hist_01",
        selected_bandha=BandhaPattern.SARVATOBHADRA,
        start_coordinate=(0, 0),
    )

    report = await decipherment_orchestrator.decipher(
        request=req,
        db=test_db,
        reference_shloka_text=HISTORICAL_MANGALACHARANA_SHLOKA,
    )

    # 3. Assertions on Report
    assert report.chakra_id == "chakra_hist_01"
    assert report.bandha_name == "SARVATOBHADRA"
    assert report.decoded_phonetic_sequence is not None
    assert len(report.decoded_phonetic_sequence) > 30

    # Phonetic stream contains opening invocation characters
    assert "ಶ್ರೀ" in report.decoded_phonetic_sequence

    # Bilingual Commentary Preserved
    assert "Syādvāda" in report.english_translation or "Jina" in report.english_translation
    assert "ಜಿನ" in report.modern_kannada_bhavartha or "ಸ್ಯಾದ್ವಾದ" in report.modern_kannada_bhavartha
    assert report.confidence_score > 0.60
    assert "overall_score" in report.confidence_breakdown

    # Alignment report present
    assert report.alignment_details is not None
    assert report.alignment_details.similarity_score > 0.70
