"""End-to-End PDF Document Processing Pipeline."""
import io
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import fitz  # PyMuPDF
from sqlalchemy.orm import Session

from clio.config import settings
from clio.extractors.matrix_extractor import chakra_extractor
from clio.extractors.shloka_extractor import shloka_extractor
from clio.graph.knowledge_extractor import knowledge_extractor
from clio.ingestion.ocr_engine import ocr_engine
from clio.models.chakra import ChakraMatrix
from clio.models.document import (
    DocumentMetadata,
    PageClassification,
    PageMetadata,
    ProcessingJob,
    ProcessingStatus,
)
from clio.models.graph import GraphNode, NodeType, VerificationStatus
from clio.models.shloka import Shloka
from clio.storage.db import (
    CellRecord,
    ChakraRecord,
    DocumentRecord,
    JobRecord,
    PageRecord,
    ShlokaRecord,
    SessionLocal,
)
from clio.storage.graph_store import graph_store
from clio.storage.object_store import object_store

logger = logging.getLogger(__name__)


class PDFIngestionPipeline:
    """Orchestrates PDF ingestion, classification, extraction, and graph construction."""

    def __init__(self):
        settings.ensure_directories()

    def check_duplicate(self, sha256_hash: str, db: Session) -> Optional[DocumentRecord]:
        """Check if a document with this SHA-256 hash has already been ingested."""
        return db.query(DocumentRecord).filter(DocumentRecord.sha256_hash == sha256_hash).first()

    def create_ingestion_job(
        self, filename: str, content: bytes, db: Session
    ) -> Tuple[str, str, bool]:
        """Validate, store, and initialize job for uploaded PDF.

        Returns:
            (document_id, job_id, is_duplicate)
        """
        sha256_hash = object_store.calculate_sha256(content)
        existing = self.check_duplicate(sha256_hash, db)
        if existing:
            # Check if there is an existing job
            job = db.query(JobRecord).filter(JobRecord.document_id == existing.id).first()
            job_id = job.id if job else f"job_{existing.id}"
            return existing.id, job_id, True

        doc_id, file_path = object_store.save_pdf(content, filename)
        job_id = f"job_{doc_id}"

        doc_rec = DocumentRecord(
            id=doc_id,
            filename=filename,
            sha256_hash=sha256_hash,
            file_size_bytes=len(content),
            total_pages=0,
            storage_path=file_path,
            status=ProcessingStatus.PENDING.value,
        )
        job_rec = JobRecord(
            id=job_id,
            document_id=doc_id,
            status=ProcessingStatus.PENDING.value,
            progress_percent=0.0,
            message="Queued for ingestion",
        )
        db.add(doc_rec)
        db.add(job_rec)
        db.commit()

        # Idempotently seed Document node in graph store
        doc_node = GraphNode(
            id=doc_id,
            type=NodeType.DOCUMENT,
            name=filename,
            properties={"sha256_hash": sha256_hash, "file_size_bytes": len(content)},
            source_reference=f"sha256:{sha256_hash}",
            verification_status=VerificationStatus.VERIFIED,
        )
        graph_store.upsert_node(doc_node)

        return doc_id, job_id, False

    def process_document(
        self,
        document_id: str,
        job_id: str,
        db: Optional[Session] = None,
    ) -> DocumentMetadata:
        """Execute synchronous or background processing of the ingested PDF."""
        should_close = False
        if db is None:
            init_db()
            db = SessionLocal()
            should_close = True
        try:
            doc_rec: Optional[DocumentRecord] = db.query(DocumentRecord).filter(DocumentRecord.id == document_id).first()
            job_rec: Optional[JobRecord] = db.query(JobRecord).filter(JobRecord.id == job_id).first()

            if not doc_rec or not job_rec:
                raise ValueError(f"Document or Job not found: doc={document_id}, job={job_id}")

            # Update status to PROCESSING
            doc_rec.status = ProcessingStatus.PROCESSING.value
            job_rec.status = ProcessingStatus.PROCESSING.value
            job_rec.progress_percent = 5.0
            job_rec.message = "Opening document stream"
            db.commit()

            pdf_bytes = object_store.get_file_bytes(doc_rec.storage_path)
            if not pdf_bytes:
                raise FileNotFoundError(f"PDF file missing at {doc_rec.storage_path}")

            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            total_pages = len(doc)
            doc_rec.total_pages = total_pages
            db.commit()

            pages_metadata: List[PageMetadata] = []

            for p_idx in range(total_pages):
                page_num = p_idx + 1
                page = doc.load_page(p_idx)
                page_id = f"page_{document_id}_{page_num:03d}"

                # Update progress
                progress = 10.0 + (p_idx / max(total_pages, 1)) * 80.0
                job_rec.progress_percent = round(progress, 1)
                job_rec.message = f"Processing page {page_num} of {total_pages}"
                db.commit()

                # 1. Render page image
                image_bytes = ocr_engine.render_page_image(page)
                image_path = object_store.save_page_image(image_bytes, document_id, page_num)

                # 2. Scanned page detection
                is_scanned, has_embedded, raw_text, char_count = ocr_engine.detect_scanned_page(page)

                # 3. Classify page
                classification = ocr_engine.classify_page(raw_text, image_bytes)

                # 4. Extract blocks with bounding boxes
                blocks = ocr_engine.extract_blocks_with_coordinates(page)

                page_meta = PageMetadata(
                    page_id=page_id,
                    document_id=document_id,
                    page_number=page_num,
                    classification=classification,
                    has_embedded_text=has_embedded,
                    is_scanned=is_scanned,
                    image_path=image_path,
                    width=page.rect.width,
                    height=page.rect.height,
                    dpi=settings.render_dpi,
                    char_count=char_count,
                    raw_text=raw_text,
                    confidence_score=0.98 if has_embedded else 0.80,
                    bounding_boxes=blocks,
                )
                pages_metadata.append(page_meta)

                # Upsert PageRecord in DB
                page_rec = PageRecord(
                    id=page_id,
                    document_id=document_id,
                    page_number=page_num,
                    classification=classification.value,
                    has_embedded_text=has_embedded,
                    is_scanned=is_scanned,
                    image_path=image_path,
                    width=page.rect.width,
                    height=page.rect.height,
                    dpi=settings.render_dpi,
                    char_count=char_count,
                    raw_text=raw_text,
                    confidence_score=page_meta.confidence_score,
                    bounding_boxes_json=json.dumps(blocks),
                )
                db.add(page_rec)
                db.flush()

                # 5. Extract Chakras if page is NUMERICAL_MATRIX or contains grid data
                if classification in (PageClassification.NUMERICAL_MATRIX, PageClassification.MIXED_CONTENT):
                    self._extract_and_save_chakras(
                        raw_text=raw_text,
                        image_bytes=image_bytes,
                        document_id=document_id,
                        page_id=page_id,
                        image_path=image_path,
                        page_rect=[0.0, 0.0, page.rect.width, page.rect.height],
                        db=db,
                    )

                # 6. Extract Shlokas if page has Kannada verses
                if classification in (PageClassification.SHLOKA, PageClassification.MIXED_CONTENT, PageClassification.COMMENTARY):
                    self._extract_and_save_shlokas(
                        raw_text=raw_text,
                        document_id=document_id,
                        page_id=page_id,
                        db=db,
                    )

                # 7. Extract Knowledge Graph entities, passages, evidence, and hypotheses
                knowledge_extractor.extract_from_page(
                    document_id=document_id,
                    page_id=page_id,
                    page_number=page_num,
                    raw_text=raw_text,
                    classification=classification.value,
                )

            # Mark COMPLETED
            doc_rec.status = ProcessingStatus.COMPLETED.value
            doc_rec.processed_at = datetime.utcnow()
            job_rec.status = ProcessingStatus.COMPLETED.value
            job_rec.progress_percent = 100.0
            job_rec.message = "Ingestion and extraction successfully completed."
            db.commit()

            return DocumentMetadata(
                document_id=doc_rec.id,
                filename=doc_rec.filename,
                sha256_hash=doc_rec.sha256_hash,
                file_size_bytes=doc_rec.file_size_bytes,
                total_pages=doc_rec.total_pages,
                storage_path=doc_rec.storage_path,
                status=ProcessingStatus.COMPLETED,
                uploaded_at=doc_rec.uploaded_at,
                processed_at=doc_rec.processed_at,
                pages=pages_metadata,
            )

        except Exception as e:
            logger.exception("Ingestion failed for doc %s: %s", document_id, e)
            db.rollback()
            try:
                doc_rec = db.query(DocumentRecord).filter(DocumentRecord.id == document_id).first()
                job_rec = db.query(JobRecord).filter(JobRecord.id == job_id).first()
                if doc_rec:
                    doc_rec.status = ProcessingStatus.FAILED.value
                    doc_rec.error_message = str(e)
                if job_rec:
                    job_rec.status = ProcessingStatus.FAILED.value
                    job_rec.error = str(e)
                    job_rec.message = f"Failed: {e}"
                db.commit()
            except Exception as inner_e:
                logger.error("Failed to persist error state: %s", inner_e)
            raise e
        finally:
            if should_close:
                db.close()

    def _extract_and_save_chakras(
        self,
        raw_text: str,
        image_bytes: bytes,
        document_id: str,
        page_id: str,
        image_path: str,
        page_rect: List[float],
        db: Session,
    ) -> None:
        """Parse 27x27 matrix lines and persist ChakraRecord & CellRecords."""
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        # Check if lines look like 27x27 grid rows
        grid_rows: List[List[str]] = []
        for line in lines:
            tokens = line.split()
            # If line contains multiple numerical tokens
            if len(tokens) >= 5:
                grid_rows.append(tokens)

        # If detected row count is close to 27 or 27x27
        if len(grid_rows) >= 20:
            matrix = chakra_extractor.extract_from_grid_data(
                grid_data=grid_rows,
                document_id=document_id,
                page_id=page_id,
                chakra_number=1,
                source_image_path=image_path,
                matrix_bbox=page_rect,
            )

            # Crop cells
            chakra_extractor.crop_and_store_cells(image_bytes, matrix)

            # Persist ChakraRecord
            ch_rec = ChakraRecord(
                id=matrix.chakra_id,
                document_id=document_id,
                page_id=page_id,
                chakra_number=matrix.chakra_number,
                rows=matrix.rows,
                cols=matrix.cols,
                expected_cells=matrix.expected_cells,
                total_extracted_cells=matrix.total_extracted_cells,
                is_valid=matrix.is_valid,
                flagged_cells_count=matrix.flagged_cells_count,
                validation_errors_json=json.dumps(matrix.validation_errors),
                matrix_grid_json=json.dumps(matrix.matrix_grid),
                matrix_bbox_json=json.dumps(matrix.matrix_bbox),
                source_image_path=matrix.source_image_path,
            )
            db.add(ch_rec)

            for cell in matrix.cells:
                cell_rec = CellRecord(
                    id=cell.cell_id,
                    chakra_id=matrix.chakra_id,
                    row=cell.row,
                    col=cell.col,
                    raw_value=cell.raw_value,
                    parsed_value=cell.parsed_value,
                    numeral_system=cell.numeral_system.value,
                    confidence=cell.confidence,
                    is_flagged=cell.is_flagged,
                    flag_reason=cell.flag_reason,
                    crop_path=cell.crop_path,
                    bbox_json=json.dumps(cell.bbox),
                )
                db.add(cell_rec)

            db.flush()

    def _extract_and_save_shlokas(
        self,
        raw_text: str,
        document_id: str,
        page_id: str,
        db: Session,
    ) -> None:
        """Extract Halegannada shlokas and persist ShlokaRecord."""
        # Find verse candidates (sections containing Kannada and dandas)
        blocks = raw_text.split("\n\n")
        shloka_idx = 1
        for b in blocks:
            b_clean = b.strip()
            if len(b_clean) > 20 and shloka_extractor.is_kannada_text(b_clean):
                shloka = shloka_extractor.extract_shloka(
                    raw_text=b_clean,
                    document_id=document_id,
                    page_id=page_id,
                    shloka_index=shloka_idx,
                )
                shloka_rec = ShlokaRecord(
                    id=shloka.shloka_id,
                    document_id=document_id,
                    page_id=page_id,
                    chakra_id=shloka.chakra_id,
                    is_chakra_association_uncertain=shloka.is_chakra_association_uncertain,
                    association_confidence=shloka.association_confidence,
                    shloka_number_in_page=shloka.shloka_number_in_page,
                    raw_text=shloka.raw_text,
                    normalized_unicode=shloka.normalized_unicode,
                    lines_json=json.dumps([l.model_dump() for l in shloka.lines]),
                    verse_markers_json=json.dumps(shloka.verse_markers),
                    is_manually_corrected=shloka.is_manually_corrected,
                    has_uncertain_boundaries=shloka.has_uncertain_boundaries,
                    confidence=shloka.confidence,
                    meter_name=shloka.meter_name,
                    notes=shloka.notes,
                )
                db.add(shloka_rec)
                shloka_idx += 1
        db.flush()


pdf_pipeline = PDFIngestionPipeline()
