"""Integration tests for Decipherment FastAPI endpoints."""
import json
from fastapi.testclient import TestClient
from clio.decipherment.historical_reference import (
    HISTORICAL_MANGALACHARANA_SHLOKA,
    generate_historical_chakra1_grid,
)
from clio.storage.db import ChakraRecord, DocumentRecord, PageRecord


def test_list_bandhas_endpoint(client: TestClient):
    """Verify GET /api/v1/decipher/bandhas returns documented mathematical rules."""
    res = client.get("/api/v1/decipher/bandhas")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 4

    names = [b["name"] for b in data]
    assert "SARVATOBHADRA" in names
    assert "PADMABANDHA" in names
    assert "GOMUTRIKA" in names
    assert "CHAKRABANDHA" in names

    sarv = [b for b in data if b["name"] == "SARVATOBHADRA"][0]
    assert "mathematical_rules" in sarv
    assert "kannada_name" in sarv


def test_list_tables_endpoint(client: TestClient):
    """Verify GET /api/v1/decipher/tables returns supported Ankaphala versions."""
    res = client.get("/api/v1/decipher/tables")
    assert res.status_code == 200
    data = res.json()
    assert "v1_yellappa_shastri_1953" in data["supported_versions"]


def test_execute_decipherment_endpoint(client: TestClient, test_db):
    """Verify POST /api/v1/decipher executes the pipeline over HTTP."""
    # Seed Chakra in test_db
    doc_rec = DocumentRecord(
        id="doc_api_hist",
        filename="Chakra1_1953.pdf",
        sha256_hash="1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff",
        file_size_bytes=50000,
        total_pages=1,
        storage_path="data/pdfs/c1.pdf",
        status="COMPLETED",
    )
    page_rec = PageRecord(
        id="page_api_01",
        document_id=doc_rec.id,
        page_number=1,
    )
    grid = generate_historical_chakra1_grid()
    ch_rec = ChakraRecord(
        id="chakra_api_01",
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

    # Call POST /api/v1/decipher
    res = client.post(
        "/api/v1/decipher",
        json={
            "chakra_id": "chakra_api_01",
            "selected_bandha": "SARVATOBHADRA",
            "reference_shloka_text": HISTORICAL_MANGALACHARANA_SHLOKA,
        },
    )
    assert res.status_code == 200
    report = res.json()
    assert report["chakra_id"] == "chakra_api_01"
    assert report["bandha_name"] == "SARVATOBHADRA"
    assert "decoded_phonetic_sequence" in report
    assert "english_translation" in report
    assert "modern_kannada_bhavartha" in report
    assert "confidence_score" in report
    assert report["confidence_score"] > 0.60

