"""Document and ingestion job models."""
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ProcessingStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PageClassification(str, Enum):
    NUMERICAL_MATRIX = "NUMERICAL_MATRIX"
    SHLOKA = "SHLOKA"
    COMMENTARY = "COMMENTARY"
    MIXED_CONTENT = "MIXED_CONTENT"
    UNKNOWN = "UNKNOWN"


class PageMetadata(BaseModel):
    """Metadata for a single rendered/extracted page."""
    page_id: str
    document_id: str
    page_number: int
    classification: PageClassification = PageClassification.UNKNOWN
    has_embedded_text: bool = False
    is_scanned: bool = True
    image_path: Optional[str] = None
    width: float = 0.0
    height: float = 0.0
    dpi: int = 300
    char_count: int = 0
    raw_text: Optional[str] = None
    confidence_score: float = 1.0
    bounding_boxes: List[dict] = Field(default_factory=list)


class DocumentMetadata(BaseModel):
    """Metadata for an ingested PDF document."""
    document_id: str
    filename: str
    sha256_hash: str
    file_size_bytes: int
    total_pages: int
    storage_path: str
    status: ProcessingStatus = ProcessingStatus.PENDING
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    pages: List[PageMetadata] = Field(default_factory=list)


class ProcessingJob(BaseModel):
    """Background ingestion tracking job."""
    job_id: str
    document_id: str
    status: ProcessingStatus = ProcessingStatus.PENDING
    progress_percent: float = 0.0
    message: str = "Initialized"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None

