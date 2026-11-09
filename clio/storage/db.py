"""Relational database models and session management for PostgreSQL/SQLite."""
from datetime import datetime
import json
from typing import Generator, List, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session

from clio.config import settings

Base = declarative_base()


class DocumentRecord(Base):
    __tablename__ = "documents"

    id = Column(String(64), primary_key=True)
    filename = Column(String(255), nullable=False)
    sha256_hash = Column(String(64), unique=True, index=True, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    total_pages = Column(Integer, default=0)
    storage_path = Column(String(512), nullable=False)
    status = Column(String(32), default="PENDING")
    error_message = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    pages = relationship("PageRecord", back_populates="document", cascade="all, delete-orphan")
    chakras = relationship("ChakraRecord", back_populates="document", cascade="all, delete-orphan")
    shlokas = relationship("ShlokaRecord", back_populates="document", cascade="all, delete-orphan")
    jobs = relationship("JobRecord", back_populates="document", cascade="all, delete-orphan")


class PageRecord(Base):
    __tablename__ = "pages"

    id = Column(String(64), primary_key=True)
    document_id = Column(String(64), ForeignKey("documents.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    classification = Column(String(32), default="UNKNOWN")
    has_embedded_text = Column(Boolean, default=False)
    is_scanned = Column(Boolean, default=True)
    image_path = Column(String(512), nullable=True)
    width = Column(Float, default=0.0)
    height = Column(Float, default=0.0)
    dpi = Column(Integer, default=300)
    char_count = Column(Integer, default=0)
    raw_text = Column(Text, nullable=True)
    confidence_score = Column(Float, default=1.0)
    bounding_boxes_json = Column(Text, default="[]")

    document = relationship("DocumentRecord", back_populates="pages")
    chakras = relationship("ChakraRecord", back_populates="page", cascade="all, delete-orphan")
    shlokas = relationship("ShlokaRecord", back_populates="page", cascade="all, delete-orphan")


class ChakraRecord(Base):
    __tablename__ = "chakras"

    id = Column(String(64), primary_key=True)
    document_id = Column(String(64), ForeignKey("documents.id"), nullable=False, index=True)
    page_id = Column(String(64), ForeignKey("pages.id"), nullable=False, index=True)
    chakra_number = Column(Integer, nullable=True)
    rows = Column(Integer, default=27)
    cols = Column(Integer, default=27)
    expected_cells = Column(Integer, default=729)
    total_extracted_cells = Column(Integer, default=0)
    is_valid = Column(Boolean, default=False)
    flagged_cells_count = Column(Integer, default=0)
    validation_errors_json = Column(Text, default="[]")
    matrix_grid_json = Column(Text, default="[]")
    matrix_bbox_json = Column(Text, default="[]")
    source_image_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("DocumentRecord", back_populates="chakras")
    page = relationship("PageRecord", back_populates="chakras")
    cells = relationship("CellRecord", back_populates="chakra", cascade="all, delete-orphan")


class CellRecord(Base):
    __tablename__ = "chakra_cells"

    id = Column(String(64), primary_key=True)
    chakra_id = Column(String(64), ForeignKey("chakras.id"), nullable=False, index=True)
    row = Column(Integer, nullable=False)
    col = Column(Integer, nullable=False)
    raw_value = Column(String(64), nullable=False)
    parsed_value = Column(Integer, nullable=True)
    numeral_system = Column(String(16), default="unknown")
    confidence = Column(Float, default=1.0)
    is_flagged = Column(Boolean, default=False)
    flag_reason = Column(String(255), nullable=True)
    crop_path = Column(String(512), nullable=True)
    bbox_json = Column(Text, default="[]")

    chakra = relationship("ChakraRecord", back_populates="cells")


class ShlokaRecord(Base):
    __tablename__ = "shlokas"

    id = Column(String(64), primary_key=True)
    document_id = Column(String(64), ForeignKey("documents.id"), nullable=False, index=True)
    page_id = Column(String(64), ForeignKey("pages.id"), nullable=False, index=True)
    chakra_id = Column(String(64), nullable=True, index=True)
    is_chakra_association_uncertain = Column(Boolean, default=False)
    association_confidence = Column(Float, default=1.0)
    shloka_number_in_page = Column(Integer, default=1)
    raw_text = Column(Text, nullable=False)
    normalized_unicode = Column(Text, nullable=False)
    lines_json = Column(Text, default="[]")
    verse_markers_json = Column(Text, default="[]")
    is_manually_corrected = Column(Boolean, default=False)
    correction_history_json = Column(Text, default="[]")
    has_uncertain_boundaries = Column(Boolean, default=False)
    bbox_json = Column(Text, default="[]")
    confidence = Column(Float, default=1.0)
    meter_name = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("DocumentRecord", back_populates="shlokas")
    page = relationship("PageRecord", back_populates="shlokas")


class JobRecord(Base):
    __tablename__ = "processing_jobs"

    id = Column(String(64), primary_key=True)
    document_id = Column(String(64), ForeignKey("documents.id"), nullable=False, index=True)
    status = Column(String(32), default="PENDING")
    progress_percent = Column(Float, default=0.0)
    message = Column(String(255), default="Initialized")
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    document = relationship("DocumentRecord", back_populates="jobs")


def get_engine():
    """Create database engine with directory ensure for SQLite."""
    settings.ensure_directories()
    # Check if database_url is SQLite or Postgres
    url = settings.sync_database_url
    if url.startswith("sqlite"):
        engine = create_engine(url, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(url, pool_pre_ping=True)
    return engine


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables if they do not exist."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency helper yielding DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

