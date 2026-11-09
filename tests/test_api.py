"""Integration and acceptance tests for FastAPI endpoints."""
from fastapi.testclient import TestClient
from tests.synthetic_data import generate_synthetic_pdf_bytes


def test_health_endpoint(client: TestClient):
    """Verify /health returns 200 OK and status."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "storage" in data


def test_end_of_day_acceptance_workflow(client: TestClient):
    """Full End-of-Day Acceptance Test:
    1. Upload synthetic PDF through FastAPI.
    2. Check job status and verify completion.
    3. Retrieve document and page metadata.
    4. Retrieve extracted 27x27 Chakra matrices.
    5. Retrieve extracted Halegannada shlokas.
    6. Execute middle-out graph traversal from anchor entity.
    """
    pdf_bytes = generate_synthetic_pdf_bytes()

    # 1. Upload PDF synchronously for deterministic acceptance
    upload_res = client.post(
        "/api/v1/documents/upload?run_synchronously=true",
        files={"file": ("manuscript_synthetic.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload_res.status_code == 202
    upload_data = upload_res.json()
    doc_id = upload_data["document_id"]
    job_id = upload_data["job_id"]
    assert doc_id.startswith("doc_")
    assert job_id.startswith("job_")

    # 2. Check Job status
    job_res = client.get(f"/api/v1/jobs/{job_id}")
    assert job_res.status_code == 200
    job_data = job_res.json()
    assert job_data["status"] == "COMPLETED"
    assert job_data["progress_percent"] == 100.0

    # 3. Retrieve Document metadata
    doc_res = client.get(f"/api/v1/documents/{doc_id}")
    assert doc_res.status_code == 200
    doc_data = doc_res.json()
    assert doc_data["total_pages"] == 3
    assert doc_data["status"] == "COMPLETED"
    assert doc_data["sha256_hash"] is not None

    # 4. Retrieve Pages
    pages_res = client.get(f"/api/v1/documents/{doc_id}/pages")
    assert pages_res.status_code == 200
    pages_data = pages_res.json()
    assert len(pages_data) == 3
    # Check that classifications are present
    classifications = [p["classification"] for p in pages_data]
    assert any("MATRIX" in c for c in classifications)
    assert any("SHLOKA" in c or "MIXED" in c for c in classifications)

    # 5. Retrieve Chakras
    chakras_res = client.get(f"/api/v1/documents/{doc_id}/chakras")
    assert chakras_res.status_code == 200
    chakras_data = chakras_res.json()
    assert len(chakras_data) >= 1
    matrix = chakras_data[0]
    assert matrix["rows"] == 27
    assert matrix["cols"] == 27
    assert matrix["expected_cells"] == 729
    assert len(matrix["matrix_grid"]) == 27

    # 6. Retrieve Shlokas
    shlokas_res = client.get(f"/api/v1/documents/{doc_id}/shlokas")
    assert shlokas_res.status_code == 200
    shlokas_data = shlokas_res.json()
    assert len(shlokas_data) >= 1
    shloka = shlokas_data[0]
    assert "raw_text" in shloka
    assert "normalized_unicode" in shloka
    assert "lines" in shloka

    # 7. Middle-Out Graph Traversal
    traverse_res = client.post(
        "/api/v1/graph/traverse",
        json={
            "anchor_id": "person_kumudendu_muni",
            "max_depth": 3,
            "direction": "BOTH",
            "include_hypotheses": True,
        },
    )
    assert traverse_res.status_code == 200
    traverse_data = traverse_res.json()
    assert traverse_data["anchor_entity"]["id"] == "person_kumudendu_muni"
    assert "connected_entities" in traverse_data
    assert "relationships" in traverse_data
    assert "paths" in traverse_data
    assert traverse_data["total_nodes"] >= 1

