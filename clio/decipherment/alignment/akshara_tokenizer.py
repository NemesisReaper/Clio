"""Kannada Akshara Tokenizer and Prosodic Weight Analyzer for Halegannada."""
import re
import unicodedata
from typing import List, Tuple

# Unicode Kannada Ranges
VIRAMA = "\u0CCD"  # ್
ANUSVARA = "\u0C82"  # ಂ
VISARGA = "\u0C83"  # ಃ
LONG_VOWELS = {"ಆ", "ಈ", "ಊ", "ೠ", "ೡ", "ಏ", "ಐ", "ಓ", "ಔ"}
LONG_MATRAS = {"ಾ", "ೀ", "ೂ", "ೄ", "ೇ", "ೈ", "ೋ", "ೌ"}

# Regex for Indic Kannada Akshara Tokenization:
# ((Consonant + Virama)* + Consonant + [VowelSign] + [Anusvara|Visarga]) | (IndependentVowel + [Anusvara|Visarga]) | non-Kannada
AKSHARA_REGEX = re.compile(
    r"(?:[\u0C95-\u0CB9\u0CDE\u0CA1]\u0CCD)*"  # Optional conjunct prefixes (C + virama)*
    r"[\u0C95-\u0CB9\u0CDE\u0CA1]"            # Base Consonant
    r"[\u0CBE-\u0CCC]?"                       # Optional Vowel Matra
    r"[\u0C82\u0C83]?"                        # Optional Anusvara / Visarga
    r"|"
    r"[\u0C85-\u0C94]"                        # Independent Vowel
    r"[\u0C82\u0C83]?"                        # Optional Anusvara / Visarga
    r"|"
    r"(\|{1,2}|[\u0964\u0965])"                # Verse Danda
    r"|"
    r"\s+"                                     # Whitespace
    r"|"
    r"[^\s\u0C80-\u0CFF]"                      # Any other characters (digits, symbols)
)


class AksharaTokenizer:
    """Linguistically sound Akshara (syllable) tokenizer for Kannada & Halegannada."""

    def normalize(self, text: str) -> str:
        """Apply Unicode Canonical Composition (NFC)."""
        return unicodedata.normalize("NFC", text)

    def tokenize(self, text: str) -> List[str]:
        """Segment Kannada text into an ordered list of individual aksharas."""
        normalized = self.normalize(text)
        tokens = [m.group(0) for m in AKSHARA_REGEX.finditer(normalized) if m.group(0).strip()]
        return tokens

    def calculate_syllabic_weight(self, akshara: str, is_followed_by_conjunct: bool = False) -> int:
        """Determine prosodic weight (Chhandas Matra):
        Laghu (ಲಘು) = 1 matra
        Guru (ಗುರು) = 2 matras
        Rules:
        - Short vowels (ಅ, ಇ, ಉ, ಋ, ಎ, ಒ) without conjunct/anusvara = Laghu (1)
        - Long vowels / long matras = Guru (2)
        - Suffix with Anusvara (ಂ) or Visarga (ಃ) = Guru (2)
        - Short vowel preceding a conjunct (ಸಂಯುಕ್ತಾಕ್ಷರ) = Guru (2)
        """
        akshara_clean = akshara.strip()
        if not akshara_clean or akshara_clean in ("|", "||", "।", "॥"):
            return 0

        # Anusvara or Visarga makes it Guru
        if ANUSVARA in akshara_clean or VISARGA in akshara_clean:
            return 2

        # Preceding conjunct makes it Guru
        if is_followed_by_conjunct:
            return 2

        # Independent long vowels
        if any(v in akshara_clean for v in LONG_VOWELS):
            return 2

        # Long matras
        if any(m in akshara_clean for m in LONG_MATRAS):
            return 2

        # Default short vowel / akshara
        return 1

    def compute_matra_sequence(self, tokens: List[str]) -> List[int]:
        """Generate sequence of 1 (Laghu) and 2 (Guru) for prosodic meter analysis."""
        weights = []
        n = len(tokens)
        for i in range(n):
            curr = tokens[i]
            # Check if followed by a conjunct (contains virama)
            followed_by_conjunct = False
            if i + 1 < n and VIRAMA in tokens[i + 1]:
                followed_by_conjunct = True
            w = self.calculate_syllabic_weight(curr, followed_by_conjunct)
            if w > 0:
                weights.append(w)
        return weights


akshara_tokenizer = AksharaTokenizer()
