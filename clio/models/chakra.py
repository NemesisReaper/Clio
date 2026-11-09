"""Chakra matrix models and cell schemas."""
from enum import Enum
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field


class NumeralSystem(str, Enum):
    KANNADA = "kannada"
    ARABIC = "arabic"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class CellCoordinate(BaseModel):
    row: int = Field(..., ge=0, le=26, description="Row index from 0 to 26")
    col: int = Field(..., ge=0, le=26, description="Column index from 0 to 26")
    bbox: List[float] = Field(
        default_factory=list,
        description="Bounding box [x0, y0, x1, y1] on the page/matrix image"
    )


class ChakraCell(BaseModel):
    """Individual cell inside a 27x27 Chakra matrix."""
    cell_id: str
    chakra_id: str
    row: int = Field(..., ge=0, le=26)
    col: int = Field(..., ge=0, le=26)
    raw_value: str = Field(..., description="Raw extracted OCR string before conversion")
    parsed_value: Optional[int] = Field(
        None,
        description="Integer numerical value if successfully parsed; None if unreadable"
    )
    numeral_system: NumeralSystem = NumeralSystem.UNKNOWN
    confidence: float = Field(..., ge=0.0, le=1.0)
    is_flagged: bool = Field(False, description="Flagged for manual correction if uncertain or out-of-domain")
    flag_reason: Optional[str] = None
    crop_path: Optional[str] = Field(None, description="Path to cropped cell image for manual review")
    bbox: List[float] = Field(default_factory=list)


class ChakraMatrix(BaseModel):
    """Full 27x27 Siri Bhoovalaya Chakra matrix containing exactly 729 cells."""
    chakra_id: str
    document_id: str
    page_id: str
    chakra_number: Optional[int] = None
    rows: int = 27
    cols: int = 27
    expected_cells: int = 729
    total_extracted_cells: int = 0
    is_valid: bool = False
    validation_errors: List[str] = Field(default_factory=list)
    flagged_cells_count: int = 0
    matrix_grid: List[List[Optional[int]]] = Field(
        default_factory=list,
        description="2D array 27x27 containing parsed integer values, None for missing/unreadable"
    )
    cells: List[ChakraCell] = Field(default_factory=list)
    matrix_bbox: List[float] = Field(default_factory=list)
    source_image_path: Optional[str] = None

    def export_matrix_json(self) -> dict:
        """Export validated matrix representation to JSON-serializable dictionary."""
        return self.model_dump(mode="json")

