"""FastAPI routes for document upload, pages, chakras, shlokas, and job inspection."""
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from clio.ingestion.pdf_pipeline import pdf_pipeline
from clio.models.document import ProcessingStatus
from clio.storage.db import (
    ChakraRecord,
    DocumentRecord,
    JobRecord,
    PageRecord,
    ShlokaRecord,
    get_db,
)

router = APIRouter(prefix="/api/v1", tags=["Documents"])


@router.post("/documents/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    run_synchronously: bool = False,
    db: Session = Depends(get_db),
):
    """Upload a PDF manuscript or document for digitization, extraction, and graph mapping."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents are supported for ingestion.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    doc_id, job_id, is_duplicate = pdf_pipeline.create_ingestion_job(
        filename=file.filename,
        content=content,
        db=db,
    )

    if is_duplicate:
        # Document already processed or in progress
        return {
            "document_id": doc_id,
            "job_id": job_id,
            "status": "DUPLICATE_DETECTED",
            "message": "Document with identical SHA-256 hash has already been registered.",
        }

    if run_synchronously:
        # Useful for immediate deterministic test suites
        pdf_pipeline.process_document(document_id=doc_id, job_id=job_id, db=db)
        return {
            "document_id": doc_id,
            "job_id": job_id,
            "status": ProcessingStatus.COMPLETED.value,
            "message": "Document processed synchronously.",
        }
    else:
        # Asynchronous processing in background
        background_tasks.add_task(pdf_pipeline.process_document, doc_id, job_id)
        return {
            "document_id": doc_id,
            "job_id": job_id,
            "status": ProcessingStatus.PENDING.value,
            "message": "Document accepted for asynchronous ingestion and extraction.",
        }


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Inspect background ingestion progress and failures."""
    job: Optional[JobRecord] = db.query(JobRecord).filter(JobRecord.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    return {
        "job_id": job.id,
        "document_id": job.document_id,
        "status": job.status,
        "progress_percent": job.progress_percent,
        "message": job.message,
        "error": job.error,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }


@router.get("/documents/{document_id}")
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Retrieve document metadata and ingestion status."""
    doc: Optional[DocumentRecord] = (
        db.query(DocumentRecord).filter(DocumentRecord.id == document_id).first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    return {
        "document_id": doc.id,
        "filename": doc.filename,
        "sha256_hash": doc.sha256_hash,
        "file_size_bytes": doc.file_size_bytes,
        "total_pages": doc.total_pages,
        "storage_path": doc.storage_path,
        "status": doc.status,
        "uploaded_at": doc.uploaded_at,
        "processed_at": doc.processed_at,
        "error_message": doc.error_message,
    }


@router.get("/documents/{document_id}/pages")
def get_document_pages(document_id: str, db: Session = Depends(get_db)):
    """Retrieve list of pages and classifications for a document."""
    pages: List[PageRecord] = (
        db.query(PageRecord)
        .filter(PageRecord.document_id == document_id)
        .order_by(PageRecord.page_number.asc())
        .all()
    )
    if not pages:
        # Check if document exists
        doc = db.query(DocumentRecord).filter(DocumentRecord.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found.")

    return [
        {
            "page_id": p.id,
            "document_id": p.document_id,
            "page_number": p.page_number,
            "classification": p.classification,
            "has_embedded_text": p.has_embedded_text,
            "is_scanned": p.is_scanned,
            "image_path": p.image_path,
            "width": p.width,
            "height": p.height,
            "dpi": p.dpi,
            "char_count": p.char_count,
            "confidence_score": p.confidence_score,
            "bounding_boxes": json.loads(p.bounding_boxes_json or "[]"),
        }
        for p in pages
    ]


@router.get("/documents/{document_id}/chakras")
def get_document_chakras(document_id: str, db: Session = Depends(get_db)):
    """Retrieve all 27x27 Chakra matrices extracted from the document."""
    chakras: List[ChakraRecord] = (
        db.query(ChakraRecord).filter(ChakraRecord.document_id == document_id).all()
    )
    return [
        {
            "chakra_id": c.id,
            "document_id": c.document_id,
            "page_id": c.page_id,
            "chakra_number": c.chakra_number,
            "rows": c.rows,
            "cols": c.cols,
            "expected_cells": c.expected_cells,
            "total_extracted_cells": c.total_extracted_cells,
            "is_valid": c.is_valid,
            "flagged_cells_count": c.flagged_cells_count,
            "validation_errors": json.loads(c.validation_errors_json or "[]"),
            "matrix_grid": json.loads(c.matrix_grid_json or "[]"),
            "matrix_bbox": json.loads(c.matrix_bbox_json or "[]"),
            "source_image_path": c.source_image_path,
        }
        for c in chakras
    ]


@router.get("/documents/{document_id}/shlokas")
def get_document_shlokas(document_id: str, db: Session = Depends(get_db)):
    """Retrieve extracted Halegannada shlokas with raw and normalized text."""
    shlokas: List[ShlokaRecord] = (
        db.query(ShlokaRecord).filter(ShlokaRecord.document_id == document_id).all()
    )
    return [
        {
            "shloka_id": s.id,
            "document_id": s.document_id,
            "page_id": s.page_id,
            "chakra_id": s.chakra_id,
            "shloka_number_in_page": s.shloka_number_in_page,
            "raw_text": s.raw_text,
            "normalized_unicode": s.normalized_unicode,
            "lines": json.loads(s.lines_json or "[]"),
            "verse_markers": json.loads(s.verse_markers_json or "[]"),
            "is_manually_corrected": s.is_manually_corrected,
            "has_uncertain_boundaries": s.has_uncertain_boundaries,
            "confidence": s.confidence,
            "meter_name": s.meter_name,
            "notes": s.notes,
        }
        for s in shlokas
    ]
