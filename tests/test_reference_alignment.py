"""Unit tests for Halegannada akshara segmentation, sandhi resolution, and phonetic alignment."""
from clio.decipherment.alignment.akshara_tokenizer import akshara_tokenizer
from clio.decipherment.alignment.sandhi import sandhi_resolver
from clio.decipherment.alignment.aligner import halegannada_aligner, MatchType


def test_akshara_segmentation():
    """Verify linguistic segmentation of complex Halegannada conjuncts and vowels."""
    text = "ಶ್ರೀಮತ್ಪರಮ ಗಂಭೀರ"
    tokens = akshara_tokenizer.tokenize(text)

    # Tokens should preserve conjuncts: ಶ್ರೀ, ಮ, ತ್ಪ, ರ, ಮ, ಗಂ, ಭೀ, ರ
    assert "ಶ್ರೀ" in tokens
    assert any("ಗ" in t for t in tokens)
    assert any("ಭೀ" in t for t in tokens)


def test_prosodic_weight_analysis():
    """Verify matra calculation: Laghu (1) and Guru (2)."""
    # ಶ್ರೀ (long vowel) -> 2
    assert akshara_tokenizer.calculate_syllabic_weight("ಶ್ರೀ") == 2

    # ಕ (short vowel) -> 1
    assert akshara_tokenizer.calculate_syllabic_weight("ಕ") == 1

    # ಕಂ (with anusvara) -> 2
    assert akshara_tokenizer.calculate_syllabic_weight("ಕಂ") == 2


def test_sandhi_equivalence():
    """Verify Halegannada sound shift equivalence (ಱ <-> ರ and ೞ <-> ಳ)."""
    assert sandhi_resolver.are_sandhi_equivalent("ಪೆಱ", "ಪೆರ") is True
    assert sandhi_resolver.are_sandhi_equivalent("ಒಳ್ಪು", "ಒೞ್ಪು") is True


def test_phonetic_sequence_alignment_identical():
    """Verify alignment of identical verse produces 1.0 similarity and 0 mismatches."""
    verse = "ಶ್ರೀಮತ್ಪರಮ ಗಂಭೀರ ಸ್ಯಾದ್ವಾದಾಮೋಘ ಲಾಂಛನಂ ||"
    report = halegannada_aligner.align(verse, verse)

    assert report.similarity_score == 1.0
    assert report.mismatches == 0
    assert report.is_verified_match is True


def test_phonetic_sequence_alignment_with_sandhi_variant():
    """Verify alignment correctly detects and scores Halegannada Sandhi variants."""
    cand = "ಒಳ್ಪು ಪೆರತೊಂದಿಲ್ಲ"
    ref = "ಒೞ್ಪು ಪೆಱತೊಂದಿಲ್ಲ"
    report = halegannada_aligner.align(cand, ref)

    assert report.phonetic_sandhi_matches > 0
    assert report.similarity_score >= 0.85

