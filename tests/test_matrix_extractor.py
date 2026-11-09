"""Unit tests for 27x27 Chakra matrix extractor and domain validation."""
from clio.extractors.matrix_extractor import chakra_extractor
from clio.models.chakra import NumeralSystem
from tests.synthetic_data import generate_synthetic_27x27_grid


def test_parse_kannada_and_arabic_numerals():
    """Verify parsing of Kannada and Arabic numerals within Siri Bhoovalaya domain."""
    # Kannada ೧ -> 1
    val, num_sys, conf, flag = chakra_extractor.parse_numeral("೧")
    assert val == 1
    assert num_sys == NumeralSystem.KANNADA
    assert conf >= 0.95
    assert flag is None

    # Kannada ೪೨ -> 42
    val, num_sys, conf, flag = chakra_extractor.parse_numeral("೪೨")
    assert val == 42
    assert num_sys == NumeralSystem.KANNADA
    assert conf >= 0.95
    assert flag is None

    # Arabic 64 -> 64
    val, num_sys, conf, flag = chakra_extractor.parse_numeral("64")
    assert val == 64
    assert num_sys == NumeralSystem.ARABIC
    assert conf >= 0.95
    assert flag is None


def test_out_of_domain_flagging():
    """Verify that numbers outside the documented domain are flagged and not silently accepted."""
    # 999 is outside extended domain [1, 729]
    val, num_sys, conf, flag = chakra_extractor.parse_numeral("999")
    assert val == 999
    assert conf < 0.50
    assert flag is not None
    assert "out of documented domain" in flag

    # 100 is outside primary 64-akshara domain but in extended domain <= 729
    val, num_sys, conf, flag = chakra_extractor.parse_numeral("100")
    assert val == 100
    assert flag is not None
    assert "outside primary 64-akshara domain" in flag


def test_unreadable_cells_not_silently_filled():
    """Strict test: missing/unreadable cells must NEVER be silently filled."""
    val, num_sys, conf, flag = chakra_extractor.parse_numeral("???")
    assert val is None
    assert flag is not None

    val, num_sys, conf, flag = chakra_extractor.parse_numeral("")
    assert val is None
    assert flag == "Empty cell content"


def test_full_27x27_matrix_validation():
    """Verify validation of a complete 27x27 (729 cells) matrix."""
    grid_data = generate_synthetic_27x27_grid()
    matrix = chakra_extractor.extract_from_grid_data(
        grid_data=grid_data,
        document_id="doc_test_123",
        page_id="page_test_001",
        chakra_number=1,
    )

    assert matrix.rows == 27
    assert matrix.cols == 27
    assert matrix.expected_cells == 729
    assert matrix.total_extracted_cells == 729
    assert matrix.is_valid is True
    assert len(matrix.cells) == 729
    assert matrix.flagged_cells_count == 0

    # Test JSON export capability
    exported = matrix.export_matrix_json()
    assert exported["chakra_id"] == "chakra_page_test_001_01"
    assert len(exported["cells"]) == 729
    assert len(exported["matrix_grid"]) == 27


def test_invalid_dimension_detection():
    """Detect matrices that fail the 27x27 geometry check."""
    # 26 rows instead of 27
    grid_data = generate_synthetic_27x27_grid()[:-1]
    matrix = chakra_extractor.extract_from_grid_data(
        grid_data=grid_data,
        document_id="doc_test_123",
        page_id="page_test_001",
    )
    assert matrix.is_valid is False
    assert any("expected 27" in err for err in matrix.validation_errors)

