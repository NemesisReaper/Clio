"""27x27 Chakra Matrix Extractor and Domain Validator for Siri Bhoovalaya."""
import io
import json
import logging
import re
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from PIL import Image

from clio.config import settings
from clio.models.chakra import (
    CellCoordinate,
    ChakraCell,
    ChakraMatrix,
    NumeralSystem,
)
from clio.storage.object_store import object_store

logger = logging.getLogger(__name__)

# Kannada to Arabic Digit Mapping
KANNADA_DIGIT_MAP = {
    "\u0CE6": "0",  # ೦
    "\u0CE7": "1",  # ೧
    "\u0CE8": "2",  # ೨
    "\u0CE9": "3",  # ೩
    "\u0CEA": "4",  # ೪
    "\u0CEB": "5",  # ೫
    "\u0CEC": "6",  # ೬
    "\u0CED": "7",  # ೭
    "\u0CEE": "8",  # ೮
    "\u0CEF": "9",  # ೯
}


class ChakraMatrixExtractor:
    """Detects, crops, parses, and validates 27x27 Chakra matrices."""

    def __init__(self):
        self.rows = settings.matrix_grid_dimension  # 27
        self.cols = settings.matrix_grid_dimension  # 27
        self.expected_cells = settings.matrix_expected_cell_count  # 729
        self.domain_min = settings.matrix_domain_min  # 1
        self.domain_max = settings.matrix_domain_max  # 64
        self.extended_domain_max = settings.matrix_domain_extended_max  # 729

    def parse_numeral(self, raw_str: str) -> Tuple[Optional[int], NumeralSystem, float, Optional[str]]:
        """Parse raw OCR string supporting Kannada and Arabic numerals.

        Returns:
            (parsed_integer_or_None, numeral_system, confidence, flag_reason)
        """
        cleaned = raw_str.strip()
        if not cleaned:
            return None, NumeralSystem.UNKNOWN, 0.0, "Empty cell content"

        has_kannada = any(ch in KANNADA_DIGIT_MAP for ch in cleaned)
        has_arabic = any("0" <= ch <= "9" for ch in cleaned)

        # Detect numeral system
        if has_kannada and has_arabic:
            system = NumeralSystem.MIXED
        elif has_kannada:
            system = NumeralSystem.KANNADA
        elif has_arabic:
            system = NumeralSystem.ARABIC
        else:
            return None, NumeralSystem.UNKNOWN, 0.2, f"Unrecognized non-numerical symbol: '{cleaned}'"

        # Convert Kannada digits to Arabic digits for numerical evaluation
        converted = ""
        for ch in cleaned:
            if ch in KANNADA_DIGIT_MAP:
                converted += KANNADA_DIGIT_MAP[ch]
            elif ch.isdigit():
                converted += ch
            elif ch in (" ", "\n", "\t"):
                continue
            else:
                # Disallow unexpected non-digit characters without silent strip
                return (
                    None,
                    system,
                    0.3,
                    f"Ambiguous characters in cell: '{cleaned}'",
                )

        try:
            val = int(converted)
        except ValueError:
            return None, system, 0.2, f"Failed integer parse from: '{cleaned}'"

        # Domain validation against Siri Bhoovalaya 64-akshara domain
        if self.domain_min <= val <= self.domain_max:
            # Primary valid domain [1, 64]
            return val, system, 0.98 if system != NumeralSystem.MIXED else 0.85, None
        elif self.domain_max < val <= self.extended_domain_max:
            # Extended valid domain [65, 729] (bandha coordinates / line indices)
            return (
                val,
                system,
                0.90,
                f"Value {val} outside primary 64-akshara domain (in extended domain <= 729)",
            )
        else:
            # Out of bounds
            return (
                val,
                system,
                0.40,
                f"Value {val} out of documented domain [{self.domain_min}, {self.extended_domain_max}]",
            )

    def extract_from_grid_data(
        self,
        grid_data: List[List[str]],
        document_id: str,
        page_id: str,
        chakra_number: Optional[int] = None,
        source_image_path: Optional[str] = None,
        matrix_bbox: Optional[List[float]] = None,
    ) -> ChakraMatrix:
        """Construct and strictly validate a 27x27 matrix from raw 2D string extractions.

        Crucial rule: Do NOT silently fill missing or unreadable cells.
        """
        chakra_id = f"chakra_{page_id}_{chakra_number or 1:02d}"
        extracted_cells: List[ChakraCell] = []
        validation_errors: List[str] = []
        matrix_grid: List[List[Optional[int]]] = []
        flagged_count = 0

        # Validate outer matrix dimensions
        actual_rows = len(grid_data)
        if actual_rows != self.rows:
            validation_errors.append(
                f"Invalid row count: expected {self.rows}, detected {actual_rows}"
            )

        for r_idx in range(self.rows):
            row_ints: List[Optional[int]] = []
            row_raw = grid_data[r_idx] if r_idx < actual_rows else []
            actual_cols = len(row_raw)

            if actual_cols != self.cols:
                validation_errors.append(
                    f"Row {r_idx} invalid column count: expected {self.cols}, detected {actual_cols}"
                )

            for c_idx in range(self.cols):
                raw_val = row_raw[c_idx] if c_idx < actual_cols else ""
                cell_id = f"cell_{chakra_id}_r{r_idx:02d}_c{c_idx:02d}"

                parsed_val, num_sys, conf, flag_reason = self.parse_numeral(raw_val)

                is_flagged = flag_reason is not None or parsed_val is None
                if is_flagged:
                    flagged_count += 1

                # Generate synthetic/proportional cell bounding box if outer matrix_bbox provided
                cell_bbox: List[float] = []
                if matrix_bbox and len(matrix_bbox) == 4:
                    x0, y0, x1, y1 = matrix_bbox
                    cell_w = (x1 - x0) / self.cols
                    cell_h = (y1 - y0) / self.rows
                    cell_bbox = [
                        round(x0 + c_idx * cell_w, 2),
                        round(y0 + r_idx * cell_h, 2),
                        round(x0 + (c_idx + 1) * cell_w, 2),
                        round(y0 + (r_idx + 1) * cell_h, 2),
                    ]

                cell = ChakraCell(
                    cell_id=cell_id,
                    chakra_id=chakra_id,
                    row=r_idx,
                    col=c_idx,
                    raw_value=raw_val,
                    parsed_value=parsed_val,
                    numeral_system=num_sys,
                    confidence=conf,
                    is_flagged=is_flagged,
                    flag_reason=flag_reason,
                    crop_path=None,
                    bbox=cell_bbox,
                )
                extracted_cells.append(cell)
                row_ints.append(parsed_val)

            matrix_grid.append(row_ints)

        total_extracted = len(extracted_cells)
        if total_extracted != self.expected_cells:
            validation_errors.append(
                f"Total cells mismatch: expected {self.expected_cells}, got {total_extracted}"
            )

        if flagged_count > 0:
            validation_errors.append(
                f"{flagged_count} cells flagged for manual review due to ambiguity, illegibility, or domain bounds"
            )

        is_valid = len(validation_errors) == 0

        return ChakraMatrix(
            chakra_id=chakra_id,
            document_id=document_id,
            page_id=page_id,
            chakra_number=chakra_number,
            rows=self.rows,
            cols=self.cols,
            expected_cells=self.expected_cells,
            total_extracted_cells=total_extracted,
            is_valid=is_valid,
            validation_errors=validation_errors,
            flagged_cells_count=flagged_count,
            matrix_grid=matrix_grid,
            cells=extracted_cells,
            matrix_bbox=matrix_bbox or [0.0, 0.0, 1000.0, 1000.0],
            source_image_path=source_image_path,
        )

    def crop_and_store_cells(
        self,
        image_bytes: bytes,
        matrix: ChakraMatrix,
    ) -> None:
        """Crops each 27x27 cell from page image and stores to object storage."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            w, h = img.size
            x0, y0, x1, y1 = matrix.matrix_bbox

            cell_w = (x1 - x0) / self.cols
            cell_h = (y1 - y0) / self.rows

            for cell in matrix.cells:
                cx0 = max(0, int(x0 + cell.col * cell_w))
                cy0 = max(0, int(y0 + cell.row * cell_h))
                cx1 = min(w, int(x0 + (cell.col + 1) * cell_w))
                cy1 = min(h, int(y0 + (cell.row + 1) * cell_h))

                cell_crop = img.crop((cx0, cy0, cx1, cy1))
                buf = io.BytesIO()
                cell_crop.save(buf, format="PNG")
                crop_path = object_store.save_cell_crop(
                    buf.getvalue(), matrix.chakra_id, cell.row, cell.col
                )
                cell.crop_path = crop_path
        except Exception as e:
            logger.error("Failed to crop cell images: %s", e)


chakra_extractor = ChakraMatrixExtractor()
