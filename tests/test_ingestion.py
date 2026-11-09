"""Unit and integration tests for PDF document ingestion pipeline."""
import fitz
from clio.ingestion.ocr_engine import ocr_engine
from clio.ingestion.pdf_pipeline import pdf_pipeline
from clio.models.document import PageClassification, ProcessingStatus
from clio.storage.object_store import object_store
from tests.synthetic_data import generate_synthetic_pdf_bytes


def test_sha256_hash_and_storage(tmp_path):
    """Verify document SHA-256 calculation and file persistence."""
    pdf_bytes = generate_synthetic_pdf_bytes()
    sha256 = object_store.calculate_sha256(pdf_bytes)
    assert len(sha256) == 64

    doc_id, path = object_store.save_pdf(pdf_bytes, "test.pdf")
    assert doc_id.startswith("doc_")
    retrieved = object_store.get_file_bytes(path)
    assert retrieved == pdf_bytes


def test_page_rendering_and_classification():
    """Verify high-DPI page rendering and page classification."""
    pdf_bytes = generate_synthetic_pdf_bytes()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    assert len(doc) == 3

    # Page 1: 27x27 Matrix
    p1 = doc.load_page(0)
    p1_img = ocr_engine.render_page_image(p1)
    assert len(p1_img) > 1000  # High-res PNG bytes
    p1_text = p1.get_text()
    p1_cls = ocr_engine.classify_page(p1_text, p1_img)
    assert p1_cls in (PageClassification.NUMERICAL_MATRIX, PageClassification.MIXED_CONTENT)

    # Page 2: Shlokas
    p2 = doc.load_page(1)
    p2_text = p2.get_text()
    p2_cls = ocr_engine.classify_page(p2_text)
    assert p2_cls in (PageClassification.SHLOKA, PageClassification.MIXED_CONTENT)

    # Page 3: Commentary
    p3 = doc.load_page(2)
    p3_text = p3.get_text()
    p3_cls = ocr_engine.classify_page(p3_text)
    assert p3_cls in (PageClassification.COMMENTARY, PageClassification.MIXED_CONTENT)


def test_full_pipeline_processing(test_db):
    """Verify end-to-end processing of synthetic PDF through the pipeline."""
    pdf_bytes = generate_synthetic_pdf_bytes()

    # Create job
    doc_id, job_id, is_duplicate = pdf_pipeline.create_ingestion_job(
        filename="synthetic_test.pdf",
        content=pdf_bytes,
        db=test_db,
    )
    assert is_duplicate is False

    # Prevent duplicate
    doc_id2, job_id2, is_duplicate2 = pdf_pipeline.create_ingestion_job(
        filename="synthetic_test.pdf",
        content=pdf_bytes,
        db=test_db,
    )
    assert is_duplicate2 is True
    assert doc_id2 == doc_id

    # Execute processing
    meta = pdf_pipeline.process_document(document_id=doc_id, job_id=job_id, db=test_db)
    assert meta.status == ProcessingStatus.COMPLETED
    assert meta.total_pages == 3
    assert len(meta.pages) == 3
