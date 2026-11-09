"""Halegannada (Old Kannada) Shloka Extractor and Linguistic Preservation Engine.

Preserves verbatim historical text and Unicode normalization separately without
modernizing archaic Halegannada vocabulary or altering phonemes (e.g. ಱ, ೞ).
"""
import re
import unicodedata
from typing import List, Optional, Tuple
from clio.models.shloka import Shloka, VerseLine


class HalegannadaShlokaExtractor:
    """Extracts, segments, and normalizes Halegannada verses while maintaining historical fidelity."""

    # Verse boundary delimiters: ASCII pipe |, Devanagari/Indic danda ।, double danda ॥
    DANDA_PATTERN = re.compile(r"(\|{1,2}|[\u0964\u0965]+)")
    # Indic verse numbering pattern (e.g., || ೧ ||, || 1 ||, ॥ ೪೨ ॥)
    VERSE_MARKER_PATTERN = re.compile(r"(\|{1,2}|[\u0964\u0965])\s*([0-9\u0CE6-\u0CEF]+)\s*(\|{1,2}|[\u0964\u0965])")

    # Archaic Halegannada phonemes & grammatical cues that indicate high historical authenticity
    HALEGANNADA_MARKERS = [
        "\u0CA1",  # ಱ (RRA)
        "\u0CDE",  # ೞ (LLA)
        "ದಪುದು", "ಗುಂ", "ಅಂ", "ಇಂ", "ಒಳ್", "ಪೆಱ", "ಕಂಡಪುದು", "ಎಂದೊಡೆ"
    ]

    def normalize_unicode(self, text: str) -> str:
        """Apply Unicode Canonical Composition (NFC) separately from raw text."""
        return unicodedata.normalize("NFC", text)

    def is_kannada_text(self, text: str) -> bool:
        """Check if string contains Kannada Unicode characters (U+0C80 to U+0CFF)."""
        return any("\u0C80" <= ch <= "\u0CFF" for ch in text)

    def extract_verse_markers(self, text: str) -> List[str]:
        """Extract verse markers and danda notations."""
        markers = []
        for match in self.VERSE_MARKER_PATTERN.finditer(text):
            markers.append(match.group(0))
        for match in self.DANDA_PATTERN.finditer(text):
            val = match.group(0)
            if val not in markers:
                markers.append(val)
        return markers

    def segment_lines(
        self, raw_text: str, default_bbox: Optional[List[float]] = None
    ) -> Tuple[List[VerseLine], bool]:
        """Segment shloka into verse lines, preserving raw vs normalized forms.

        Returns:
            (lines, has_uncertain_boundaries)
        """
        raw_lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        has_uncertain = False
        parsed_lines: List[VerseLine] = []

        # If text is single block without newlines, segment by danda
        if len(raw_lines) <= 1:
            tokens = self.DANDA_PATTERN.split(raw_text)
            if len(tokens) > 1:
                accum = ""
                idx = 1
                for token in tokens:
                    if self.DANDA_PATTERN.match(token):
                        accum += " " + token
                        norm = self.normalize_unicode(accum.strip())
                        d_cnt = len(self.DANDA_PATTERN.findall(accum))
                        parsed_lines.append(
                            VerseLine(
                                line_number=idx,
                                raw_text=accum.strip(),
                                normalized_text=norm,
                                danda_count=d_cnt,
                                verse_markers=self.DANDA_PATTERN.findall(accum),
                                is_uncertain_boundary=False,
                                bbox=default_bbox or [0.0, 0.0, 0.0, 0.0],
                                confidence=0.95,
                            )
                        )
                        accum = ""
                        idx += 1
                    else:
                        accum += token
                if accum.strip():
                    norm = self.normalize_unicode(accum.strip())
                    parsed_lines.append(
                        VerseLine(
                            line_number=idx,
                            raw_text=accum.strip(),
                            normalized_text=norm,
                            danda_count=0,
                            verse_markers=[],
                            is_uncertain_boundary=True,
                            bbox=default_bbox or [0.0, 0.0, 0.0, 0.0],
                            confidence=0.75,
                        )
                    )
                    has_uncertain = True
            else:
                norm = self.normalize_unicode(raw_text.strip())
                parsed_lines.append(
                    VerseLine(
                        line_number=1,
                        raw_text=raw_text.strip(),
                        normalized_text=norm,
                        danda_count=0,
                        verse_markers=[],
                        is_uncertain_boundary=True,
                        bbox=default_bbox or [0.0, 0.0, 0.0, 0.0],
                        confidence=0.80,
                    )
                )
                has_uncertain = True
        else:
            for idx, r_line in enumerate(raw_lines, start=1):
                norm = self.normalize_unicode(r_line)
                dandas = self.DANDA_PATTERN.findall(r_line)
                uncertain = len(dandas) == 0 and len(r_line) < 15
                if uncertain:
                    has_uncertain = True
                parsed_lines.append(
                    VerseLine(
                        line_number=idx,
                        raw_text=r_line,
                        normalized_text=norm,
                        danda_count=len(dandas),
                        verse_markers=dandas,
                        is_uncertain_boundary=uncertain,
                        bbox=default_bbox or [0.0, 0.0, 0.0, 0.0],
                        confidence=0.85 if uncertain else 0.98,
                    )
                )

        return parsed_lines, has_uncertain

    def detect_meter(self, text: str) -> Optional[str]:
        """Heuristic detection of common Halegannada meters (e.g. Kanda, Shatpadi)."""
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if len(lines) == 4:
            return "Kanda Padya (ಕಂದ ಪದ್ಯ)"
        elif len(lines) == 6:
            return "Bhamini/Vardhaka Shatpadi (ಷಟ್ಪದಿ)"
        return "Mukta Shloka (ಮುಕ್ತಕ ಶ್ಲೋಕ)"

    def extract_shloka(
        self,
        raw_text: str,
        document_id: str,
        page_id: str,
        shloka_index: int = 1,
        chakra_id: Optional[str] = None,
        is_chakra_association_uncertain: bool = False,
        association_confidence: float = 1.0,
        bbox: Optional[List[float]] = None,
    ) -> Shloka:
        """Create a provenance-tracked Shloka object without modernizing historical vocabulary."""
        shloka_id = f"shloka_{page_id}_{shloka_index:03d}"
        normalized = self.normalize_unicode(raw_text)
        lines, has_uncertain = self.segment_lines(raw_text, default_bbox=bbox)
        markers = self.extract_verse_markers(raw_text)
        meter = self.detect_meter(raw_text)

        # Confidence calculation based on Kannada character presence and boundary clarity
        confidence = 0.95
        if not self.is_kannada_text(raw_text):
            confidence = 0.60
        if has_uncertain:
            confidence *= 0.85

        return Shloka(
            shloka_id=shloka_id,
            document_id=document_id,
            page_id=page_id,
            chakra_id=chakra_id,
            is_chakra_association_uncertain=is_chakra_association_uncertain,
            association_confidence=association_confidence,
            shloka_number_in_page=shloka_index,
            raw_text=raw_text,
            normalized_unicode=normalized,
            lines=lines,
            verse_markers=markers,
            is_manually_corrected=False,
            correction_history=[],
            has_uncertain_boundaries=has_uncertain,
            bbox=bbox or [0.0, 0.0, 0.0, 0.0],
            confidence=round(confidence, 3),
            meter_name=meter,
            notes="Halegannada vocabulary preserved verbatim without phonetic or modern morphological alteration.",
        )


shloka_extractor = HalegannadaShlokaExtractor()

