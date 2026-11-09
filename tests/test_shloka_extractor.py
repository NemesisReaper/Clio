"""Unit tests for Halegannada shloka extraction and linguistic preservation."""
from clio.extractors.shloka_extractor import shloka_extractor


def test_verbatim_text_preservation_and_normalization():
    """Verify raw text is preserved verbatim and NFC normalization is stored separately."""
    raw_verse = "ಶ್ರೀಮತ್ಪರಮ ಗಂಭೀರ ಸ್ಯಾದ್ವಾದಾಮೋಘ ಲಾಂಛನಂ | ಜೀಯಾತ್ ತ್ರೈಲೋಕ್ಯ ನಾಥಸ್ಯ ಶಾಸನಂ ಜಿನ ಶಾಸನಂ || ೧ ||"
    shloka = shloka_extractor.extract_shloka(
        raw_text=raw_verse,
        document_id="doc_test_123",
        page_id="page_test_002",
        shloka_index=1,
    )

    assert shloka.raw_text == raw_verse
    assert shloka.normalized_unicode is not None
    # Punctuation markers extracted
    assert len(shloka.verse_markers) > 0
    # No modernization notes
    assert "Halegannada vocabulary preserved verbatim" in shloka.notes


def test_verse_line_segmentation():
    """Verify segmentation of lines and detection of verse markers."""
    multi_line = (
        "ಒಳ್ಪು ಪೆಱತೊಂದಿಲ್ಲ ಕಂಡಪುದು ಜಿನೇಂದ್ರವಾಣಿ |\n"
        "ಅಂಕದಿಂ ಪೊಣರ್ಚಿದ ಸಿರಿಭೂವಲಯದೊಳ್ ಬೆಳಗುತಿರ್ಪುದು || ೨ ||"
    )
    shloka = shloka_extractor.extract_shloka(
        raw_text=multi_line,
        document_id="doc_test_123",
        page_id="page_test_002",
        shloka_index=2,
    )

    assert len(shloka.lines) == 2
    assert shloka.lines[0].line_number == 1
    assert "ಒಳ್ಪು" in shloka.lines[0].raw_text
    assert shloka.lines[0].danda_count == 1
    assert shloka.lines[1].line_number == 2
    assert "ಸಿರಿಭೂವಲಯದೊಳ್" in shloka.lines[1].raw_text
    assert shloka.lines[1].danda_count >= 1
    assert any("||" in m for m in shloka.lines[1].verse_markers)


def test_uncertain_verse_boundaries_flagging():
    """Verify that ambiguous verses without standard dandas are flagged as uncertain."""
    ambiguous_text = "ಅಸ್ಪಷ್ಟ ಸಾಲುಗಳು ವಿವರಣೆ ಇಲ್ಲದ ಪದ್ಯ ಭಾಗ"
    shloka = shloka_extractor.extract_shloka(
        raw_text=ambiguous_text,
        document_id="doc_test_123",
        page_id="page_test_002",
        shloka_index=3,
    )

    assert shloka.has_uncertain_boundaries is True
    assert shloka.confidence < 0.90


def test_multiple_shlokas_and_uncertain_chakra_association():
    """Verify support for multiple shlokas per page and uncertain Chakra associations."""
    shloka1 = shloka_extractor.extract_shloka(
        raw_text="ಪದ್ಯ ಒಂದು |",
        document_id="doc_001",
        page_id="page_001",
        shloka_index=1,
        chakra_id="chakra_page_001_01",
        is_chakra_association_uncertain=False,
    )
    shloka2 = shloka_extractor.extract_shloka(
        raw_text="ಪದ್ಯ ಎರಡು ||",
        document_id="doc_001",
        page_id="page_001",
        shloka_index=2,
        chakra_id="chakra_page_001_01",
        is_chakra_association_uncertain=True,
        association_confidence=0.55,
    )

    assert shloka1.shloka_number_in_page == 1
    assert shloka2.shloka_number_in_page == 2
    assert shloka2.is_chakra_association_uncertain is True
    assert shloka2.association_confidence == 0.55
