"""Halegannada Shloka models and verse schemas."""
from typing import List, Optional
from pydantic import BaseModel, Field


class VerseLine(BaseModel):
    """A single metered line or segment within a shloka."""
    line_number: int
    raw_text: str = Field(..., description="Verbatim raw text before normalization")
    normalized_text: str = Field(..., description="Canonical Unicode normalized text (NFC)")
    danda_count: int = 0
    verse_markers: List[str] = Field(default_factory=list)
    is_uncertain_boundary: bool = False
    bbox: List[float] = Field(default_factory=list)
    confidence: float = 1.0


class Shloka(BaseModel):
    """Halegannada verse preserved without modernizing historical vocabulary."""
    shloka_id: str
    document_id: str
    page_id: str
    chakra_id: Optional[str] = Field(
        None,
        description="Associated Chakra ID if mapped; can be None or uncertain"
    )
    is_chakra_association_uncertain: bool = False
    association_confidence: float = 1.0
    shloka_number_in_page: int = 1
    raw_text: str = Field(..., description="Verbatim extracted raw text")
    normalized_unicode: str = Field(..., description="Standard Unicode NFC normalized text")
    lines: List[VerseLine] = Field(default_factory=list)
    verse_markers: List[str] = Field(
        default_factory=list,
        description="Preserved danda (|, ||, ।, ॥) and stanza numbers"
    )
    is_manually_corrected: bool = False
    correction_history: List[dict] = Field(default_factory=list)
    has_uncertain_boundaries: bool = False
    bbox: List[float] = Field(default_factory=list)
    confidence: float = 1.0
    meter_name: Optional[str] = Field(
        None,
        description="Identified Halegannada chhandas/meter e.g., Kanda, Vritta, Shatpadi"
    )
    notes: Optional[str] = None

