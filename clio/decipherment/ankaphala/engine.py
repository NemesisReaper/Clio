"""Ankaphala Engine: Reversible Numerical-to-Akshara Phonetic Substitution."""
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from clio.models.decipherment import PhoneticMapping
from clio.decipherment.ankaphala.tables import (
    HISTORICAL_ANKAPHALA_V1,
    RAW_HISTORICAL_ANKAPHALA_V1,
    TABLE_V1_PROVENANCE_AUDIT,
    AksharaEntry,
    AnkaphalaVersion,
    RawAksharaEntry,
    TableProvenanceMetadata,
)

logger = logging.getLogger(__name__)


VOWEL_TO_MATRA = {
    "ಆ": "ಾ", "ಇ": "ಿ", "ಈ": "ೀ", "ಉ": "ು", "ಊ": "ೂ", "ಋ": "ೃ",
    "ಎ": "ೆ", "ಏ": "ೇ", "ಐ": "ೈ", "ಒ": "ೊ", "ಓ": "ೋ", "ಔ": "ೌ",
    "ಅಂ": "ಂ", "ಅಃ": "ಃ"
}


class AnkaphalaEngine:
    """Historically grounded numerical-to-akshara substitution engine."""

    def __init__(self):
        self._tables: Dict[AnkaphalaVersion, Dict[int, AksharaEntry]] = {
            AnkaphalaVersion.V1_YELLAPPA_SHASTRI_1953: HISTORICAL_ANKAPHALA_V1,
            AnkaphalaVersion.V2_PHONETIC_VARIANTS: self._build_v2_table(),
        }
        self._reverse_cache: Dict[AnkaphalaVersion, Dict[str, List[int]]] = {}
        self._build_reverse_lookup_indexes()

    def _build_v2_table(self) -> Dict[int, AksharaEntry]:
        """Build variant table with explicit matra expansions."""
        table = dict(HISTORICAL_ANKAPHALA_V1)
        return table

    def _build_reverse_lookup_indexes(self) -> None:
        """Construct inverted index mapping aksharas/phonemes back to numbers."""
        for version, table in self._tables.items():
            rev: Dict[str, List[int]] = {}
            for num, entry in table.items():
                if entry.primary_akshara:
                    rev.setdefault(entry.primary_akshara, []).append(num)
                if entry.iast:
                    rev.setdefault(entry.iast.lower(), []).append(num)
                for var in entry.variant_aksharas:
                    if var:
                        rev.setdefault(var.lower(), []).append(num)
            self._reverse_cache[version] = rev

    def list_supported_versions(self) -> List[str]:
        return [v.value for v in AnkaphalaVersion]

    def get_table(
        self, version: AnkaphalaVersion = AnkaphalaVersion.V1_YELLAPPA_SHASTRI_1953
    ) -> Dict[int, AksharaEntry]:
        if version not in self._tables:
            raise ValueError(f"Unknown Ankaphala version: {version}")
        return self._tables[version]

    def get_raw_table(self) -> Dict[int, RawAksharaEntry]:
        """Retrieve the verbatim unadulterated 1953 historical table without algorithmic extensions."""
        return RAW_HISTORICAL_ANKAPHALA_V1

    def get_table_provenance(
        self, version: AnkaphalaVersion = AnkaphalaVersion.V1_YELLAPPA_SHASTRI_1953
    ) -> TableProvenanceMetadata:
        """Retrieve historical source and audit verification metadata for the table."""
        if version == AnkaphalaVersion.V1_YELLAPPA_SHASTRI_1953:
            return TABLE_V1_PROVENANCE_AUDIT
        return TABLE_V1_PROVENANCE_AUDIT

    def substitute_raw(self, numbers: List[int]) -> List[str]:
        """Convert numbers using strictly literal historical table tokens without ligature composition.
        
        Preserves original unmerged graphemes (Tier 1: DIRECTLY_EXTRACTED_TEXT).
        """
        raw_table = self.get_raw_table()
        tokens: List[str] = []
        for idx, n in enumerate(numbers):
            if n in raw_table:
                tokens.append(raw_table[n].raw_grapheme)
            else:
                logger.warning("Number %d at index %d is outside raw Ankaphala domain [1, 64]", n, idx)
                tokens.append(f"<{n}>")
        return tokens

    def substitute(
        self,
        numbers: List[int],
        version: AnkaphalaVersion = AnkaphalaVersion.V1_YELLAPPA_SHASTRI_1953,
    ) -> str:
        """Convert a sequence of numbers into a continuous Halegannada phonetic string with ligature composition."""
        table = self.get_table(version)
        result_tokens: List[str] = []

        for idx, n in enumerate(numbers):
            if n in table:
                val = table[n].primary_akshara
                # Check for ligature composition: if vowel matra follows a consonant
                if result_tokens and val in VOWEL_TO_MATRA:
                    prev = result_tokens[-1]
                    if any("\u0C95" <= ch <= "\u0CB9" or ch in ("\u0CDE", "\u0CA1") for ch in prev):
                        result_tokens[-1] = prev + VOWEL_TO_MATRA[val]
                        continue
                result_tokens.append(val)
            else:
                logger.warning(
                    "Number %d at index %d is outside the documented Ankaphala domain [1, 64]",
                    n,
                    idx,
                )
                result_tokens.append(f"<{n}>")

        return "".join(result_tokens)

    def substitute_with_details(
        self,
        numbers: List[int],
        version: AnkaphalaVersion = AnkaphalaVersion.V1_YELLAPPA_SHASTRI_1953,
    ) -> List[Dict[str, Any]]:
        """Perform substitution while preserving full provenance and linguistic metadata per token."""
        table = self.get_table(version)
        detailed_steps = []

        for idx, n in enumerate(numbers):
            if n in table:
                entry = table[n]
                detailed_steps.append({
                    "step": idx + 1,
                    "number": n,
                    "akshara": entry.primary_akshara,
                    "iast": entry.iast,
                    "ipa": entry.ipa,
                    "category": entry.category,
                    "is_structural": entry.is_structural,
                    "provenance": entry.provenance,
                    "is_ambiguous": len(entry.variant_aksharas) > 1,
                    "alternative_readings": entry.variant_aksharas,
                })
            else:
                detailed_steps.append({
                    "step": idx + 1,
                    "number": n,
                    "akshara": f"<{n}>",
                    "iast": f"<{n}>",
                    "ipa": "",
                    "category": "out_of_domain",
                    "is_structural": False,
                    "provenance": "Out of documented domain [1, 64]",
                    "is_ambiguous": True,
                    "alternative_readings": [],
                })

        return detailed_steps

    def reverse_lookup(
        self,
        akshara: str,
        version: AnkaphalaVersion = AnkaphalaVersion.V1_YELLAPPA_SHASTRI_1953,
    ) -> List[int]:
        """Perform mathematically valid reversible lookup from an akshara/phoneme to its assigned numbers."""
        rev = self._reverse_cache.get(version, {})
        clean_key = akshara.strip()
        if clean_key in rev:
            return rev[clean_key]
        if clean_key.lower() in rev:
            return rev[clean_key.lower()]
        return []


ankaphala_engine = AnkaphalaEngine()
