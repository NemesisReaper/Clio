"""Typed provenance, source, and rule-verification models for Siri Bhoovalaya decipherment."""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RuleVerificationState(str, Enum):
    """Explicit historical verification states for decipherment rules and tables."""
    VERIFIED = "VERIFIED"                       # Supported by an identified primary or reliable scholarly source
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"   # Source supports only part of implementation (e.g. concept attested, path inferred)
    UNVERIFIED = "UNVERIFIED"                   # No adequate source located
    EXPERIMENTAL = "EXPERIMENTAL"               # Proposed algorithm awaiting validation
    SYNTHETIC_TEST_ONLY = "SYNTHETIC_TEST_ONLY" # Created exclusively for engineering tests


class DocumentationLevel(str, Enum):
    """How directly the algorithm or data matches historical sources."""
    DIRECTLY_DOCUMENTED = "DIRECTLY_DOCUMENTED"
    INFERRED = "INFERRED"
    EXPERIMENTAL = "EXPERIMENTAL"
    SYNTHETIC = "SYNTHETIC"


class HumanVerificationStatus(str, Enum):
    """Human expert review status."""
    PENDING = "PENDING"
    VERIFIED_BY_EXPERT = "VERIFIED_BY_EXPERT"
    CONTESTED = "CONTESTED"
    REJECTED = "REJECTED"


class OutputTier(str, Enum):
    """5-tier classification of decipherment outputs."""
    DIRECTLY_EXTRACTED_TEXT = "DIRECTLY_EXTRACTED_TEXT"
    ALGORITHMICALLY_GENERATED_CANDIDATE_TEXT = "ALGORITHMICALLY_GENERATED_CANDIDATE_TEXT"
    CANDIDATE_ALIGNMENT_WITH_SHLOKA = "CANDIDATE_ALIGNMENT_WITH_SHLOKA"
    HISTORICALLY_SUPPORTED_INTERPRETATION = "HISTORICALLY_SUPPORTED_INTERPRETATION"
    SPECULATIVE_INTERPRETATION = "SPECULATIVE_INTERPRETATION"


class HistoricalSourceModel(BaseModel):
    """Bibliographic record of a historical or scholarly primary/secondary source."""
    id: str
    title: str
    authors_or_editors: str
    publication_year: Optional[int] = None
    publisher: Optional[str] = None
    city: Optional[str] = None
    edition: Optional[str] = None
    physical_location: Optional[str] = None
    isbn_or_catalog_id: Optional[str] = None
    description: Optional[str] = None
    is_primary_manuscript: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SourceEditionModel(BaseModel):
    """Specific variant edition of a historical source."""
    id: str
    source_id: str
    edition_name: str
    publication_year: int
    editor: Optional[str] = None
    notes: Optional[str] = None


class SourcePassageModel(BaseModel):
    """Specific passage, page, or table reference in a source edition."""
    id: str
    source_id: str
    edition_id: Optional[str] = None
    page_number: Optional[int] = None
    section_or_stanza: str
    transcription: Optional[str] = None
    plate_or_figure: Optional[str] = None


class RuleProvenanceModel(BaseModel):
    """Complete provenance and verification audit record for an individual decipherment rule."""
    rule_id: str
    rule_name: str
    rule_type: str  # e.g., BANDHA_TRAVERSAL, ANKAPHALA_TABLE, LIGATURE_SYNTHESIS, SANDHI_EQUIVALENCE, ALIGNMENT
    source_id: Optional[str] = None
    passage_id: Optional[str] = None
    exact_citation: str
    documentation_level: DocumentationLevel
    verification_state: RuleVerificationState
    author_or_editor: str
    publication_date: Optional[str] = None
    implementation_location: str
    test_coverage_location: str
    known_limitations: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RuleVerificationRecordModel(BaseModel):
    """Audit log of an explicit verification review."""
    id: str
    rule_id: str
    verification_state: RuleVerificationState
    verifying_authority: str
    verification_date: datetime = Field(default_factory=datetime.utcnow)
    rationale: str
    identified_discrepancies: List[str] = Field(default_factory=list)


class DeciphermentConfidenceBreakdown(BaseModel):
    """Multi-dimensional decoupled confidence metrics.
    
    Explicitly separates independent evidential dimensions instead of conflating
    linguistic plausibility with historical truth.
    """
    matrix_extraction_completeness: float = Field(..., ge=0.0, le=1.0, description="Completeness of extracted 729 cells [0..1]")
    bandha_rule_verification: RuleVerificationState
    bandha_rule_verification_score: float = Field(..., ge=0.0, le=1.0, description="Evidential score for Bandha traversal [0..1]")
    ankaphala_table_verification: RuleVerificationState
    ankaphala_table_verification_score: float = Field(..., ge=0.0, le=1.0, description="Evidential score for Ankaphala table [0..1]")
    traversal_reproducibility: float = Field(..., ge=0.0, le=1.0, description="Determinism and bounds compliance [0..1]")
    reference_alignment_quality: Optional[float] = Field(None, ge=0.0, le=1.0, description="Needleman-Wunsch similarity score [0..1]")
    historical_evidence_coverage: float = Field(..., ge=0.0, le=1.0, description="Density of primary historical citations [0..1]")
    human_verification_status: HumanVerificationStatus = HumanVerificationStatus.PENDING
    is_calibrated_heuristic: bool = True
    heuristic_composite_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Non-authoritative composite indicator only")
    disclaimer: str = (
        "This confidence breakdown reports independent evidential dimensions. "
        "High alignment quality alone does not claim or prove successful historical decipherment."
    )


class ValidationResultModel(BaseModel):
    """Output of a formal validation check on a rule, matrix, or shloka."""
    validation_id: str
    target_type: str  # RULE, CHAKRA, SHLOKA, DECIPHERMENT_RUN
    target_id: str
    is_valid: bool
    verification_state: RuleVerificationState
    validation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    provenance_chain: List[str] = Field(default_factory=list)

