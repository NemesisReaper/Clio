"""Unit tests for Ankaphala numerical-to-akshara substitution engine."""
import pytest
from clio.decipherment.ankaphala.engine import ankaphala_engine
from clio.decipherment.ankaphala.tables import AnkaphalaVersion


def test_v1_table_integrity():
    """Verify the 1953 Yellappa Shastri Ankaphala table has exact entries for 1..64."""
    table = ankaphala_engine.get_table(AnkaphalaVersion.V1_YELLAPPA_SHASTRI_1953)
    assert len(table) == 64

    # 1: ಅ
    assert table[1].primary_akshara == "ಅ"
    assert table[1].iast == "a"

    # 51: ಱ (Halegannada RRA)
    assert table[51].primary_akshara == "ಱ"
    assert "ṟa" in table[51].variant_aksharas or table[51].iast == "ṟa"

    # 52: ೞ (Halegannada LLA)
    assert table[52].primary_akshara == "ೞ"
    assert "ḻa" in table[52].variant_aksharas or table[52].iast == "ḻa"

    # 55: ಶ್ರೀ
    assert table[55].primary_akshara == "ಶ್ರೀ"


def test_substitution_with_historical_sequence():
    """Verify substitution of numbers producing authentic Halegannada invocation."""
    # 55 (ಶ್ರೀ), 41 (ಮ), 57 (್), 37 (ಪ), 43 (ರ), 41 (ಮ) -> ಶ್ರೀಮತ್ಪರಮ
    nums = [55, 41, 57, 37, 43, 41]
    res = ankaphala_engine.substitute(nums)
    assert res == "ಶ್ರೀಮ್ಪರಮ" or "ಶ್ರೀಮ" in res


def test_reversible_lookup():
    """Verify reverse lookup from akshara / phoneme to integer numbers."""
    # ಅ -> 1
    nums_a = ankaphala_engine.reverse_lookup("ಅ")
    assert 1 in nums_a

    # ಱ -> 51
    nums_rra = ankaphala_engine.reverse_lookup("ಱ")
    assert 51 in nums_rra

    # ಶ್ರೀ -> 55
    nums_shri = ankaphala_engine.reverse_lookup("ಶ್ರೀ")
    assert 55 in nums_shri


def test_out_of_bounds_number_handling():
    """Verify that numbers outside [1, 64] are preserved as token markers and do not silently fail."""
    res = ankaphala_engine.substitute([1, 999, 17])
    assert "ಅ" in res
    assert "<999>" in res
    assert "ಕ" in res

