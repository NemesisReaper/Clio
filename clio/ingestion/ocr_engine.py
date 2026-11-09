"""OCR Engine, page classification, and image processing utilities using PyMuPDF and OpenCV."""
import io
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
import cv2
import fitz  # PyMuPDF
import numpy as np
from PIL import Image

from clio.config import settings
from clio.models.document import PageClassification

logger = logging.getLogger(__name__)

# Kannada Unicode letters (excluding numerals U+0CE6-U+0CEF)
KANNADA_LETTER_REGEX = re.compile(r"[\u0C85-\u0CE5\u0CDE\u0CE1]")
# Digits in Kannada and Arabic
DIGIT_REGEX = re.compile(r"[0-9\u0CE6-\u0CEF]")
# Verse punctuation
DANDA_REGEX = re.compile(r"(\|{1,2}|[\u0964\u0965]+)")


class OCREngine:
    """Document page analyzer, classifier, and OCR preprocessor."""

    def __init__(self, render_dpi: int = 300):
        self.dpi = render_dpi

    def render_page_image(self, page: fitz.Page) -> bytes:
        """Render PyMuPDF page to high-resolution PNG bytes."""
        pix = page.get_pixmap(dpi=self.dpi)
        return pix.tobytes("png")

    def detect_scanned_page(self, page: fitz.Page) -> Tuple[bool, bool, str, int]:
        """Detect whether a page is scanned or contains native embedded text.

        Returns:
            (is_scanned, has_embedded_text, extracted_text, char_count)
        """
        raw_text = page.get_text("text").strip()
        char_count = len(raw_text)

        # If char_count is very low or page consists primarily of raster images
        image_list = page.get_images()
        is_scanned = char_count < 30 and len(image_list) > 0
        has_embedded_text = char_count >= 15

        return is_scanned, has_embedded_text, raw_text, char_count

    def extract_blocks_with_coordinates(
        self, page: fitz.Page
    ) -> List[Dict[str, Any]]:
        """Extract text blocks with bounding boxes and line coordinates."""
        blocks = []
        raw_blocks = page.get_text("blocks")
        for b in raw_blocks:
            # b: (x0, y0, x1, y1, text, block_no, block_type)
            if len(b) >= 5:
                text = str(b[4]).strip()
                if text:
                    # Calculate uncertainty score based on irregular or replacement characters
                    uncertain = "\ufffd" in text or "?" in text
                    confidence = 0.70 if uncertain else 0.99
                    blocks.append(
                        {
                            "bbox": [round(b[0], 2), round(b[1], 2), round(b[2], 2), round(b[3], 2)],
                            "text": text,
                            "confidence": confidence,
                            "is_uncertain": uncertain,
                        }
                    )
        return blocks

    def classify_page(
        self, raw_text: str, image_bytes: Optional[bytes] = None
    ) -> PageClassification:
        """Classify page into NUMERICAL_MATRIX, SHLOKA, COMMENTARY, or MIXED_CONTENT."""
        # 1. Analyze text token distribution
        tokens = raw_text.split()
        total_tokens = len(tokens)
        if total_tokens == 0 and image_bytes:
            # Analyze image layout directly
            return self._classify_image_layout(image_bytes)

        num_digit_tokens = sum(1 for t in tokens if DIGIT_REGEX.search(t))
        num_kannada_letters = len(KANNADA_LETTER_REGEX.findall(raw_text))
        has_dandas = bool(DANDA_REGEX.search(raw_text))

        # Check for 27x27 matrix indicators: high density of numbers
        digit_ratio = num_digit_tokens / max(total_tokens, 1)

        if num_digit_tokens >= 40 or digit_ratio > 0.40:
            if num_kannada_letters > 60:
                return PageClassification.MIXED_CONTENT
            return PageClassification.NUMERICAL_MATRIX

        if has_dandas and num_kannada_letters > 20:
            if len(raw_text) > 400:
                return PageClassification.MIXED_CONTENT
            return PageClassification.SHLOKA

        if num_kannada_letters > 30 or total_tokens > 20:
            return PageClassification.COMMENTARY

        return PageClassification.MIXED_CONTENT

    def _classify_image_layout(self, image_bytes: bytes) -> PageClassification:
        """Classify page layout from raster image using OpenCV line/grid detection."""
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
            if img is None:
                return PageClassification.UNKNOWN

            # Adaptive threshold
            thresh = cv2.adaptiveThreshold(
                img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 2
            )

            # Detect horizontal and vertical lines
            scale = 20
            h_size = int(thresh.shape[1] / scale)
            h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_size, 1))
            h_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel)

            v_size = int(thresh.shape[0] / scale)
            v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_size))
            v_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel)

            grid_mask = cv2.add(h_lines, v_lines)
            grid_pixels = cv2.countNonZero(grid_mask)

            # If strong grid lines present
            if grid_pixels > (img.shape[0] * img.shape[1] * 0.02):
                return PageClassification.NUMERICAL_MATRIX
            return PageClassification.COMMENTARY
        except Exception as e:
            logger.warning("Image layout classification failed: %s", e)
            return PageClassification.UNKNOWN


ocr_engine = OCREngine()
