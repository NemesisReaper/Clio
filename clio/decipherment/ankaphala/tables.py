"""Historically documented Ankaphala (numerical-to-akshara) mapping tables.

Sources:
1. "Siri Bhoovalaya of Kumudendu Muni", Edited by K. Yellappa Shastri &
   Karlamangalam Srikantaiah, Central Jain Board, Bangalore, 1953.
2. Classical 64-Akshara Jain Canonical Lipi tradition.
"""
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class AnkaphalaVersion(str, Enum):
    V1_YELLAPPA_SHASTRI_1953 = "v1_yellappa_shastri_1953"
    V2_PHONETIC_VARIANTS = "v2_phonetic_variants"


class AksharaEntry(BaseModel):
    """Detailed metadata for a single Ankaphala numerical assignment."""
    number: int = Field(..., ge=1, le=64)
    primary_akshara: str
    variant_aksharas: List[str] = Field(default_factory=list)
    vowel_matra: Optional[str] = None
    iast: str
    ipa: str
    category: str
    provenance: str
    is_structural: bool = False


# Canonical 64-Akshara Siri Bhoovalaya Table (Yellappa Shastri 1953 Edition)
HISTORICAL_ANKAPHALA_V1: Dict[int, AksharaEntry] = {
    # 1-16: Svaras (Vowels) and Yogavahas
    1: AksharaEntry(
        number=1, primary_akshara="ಅ", variant_aksharas=["a"], iast="a", ipa="ʌ",
        category="svara_short", provenance="Yellappa Shastri 1953, Table 1 (p. 24)"
    ),
    2: AksharaEntry(
        number=2, primary_akshara="ಆ", variant_aksharas=["ಾ", "ā"], vowel_matra="ಾ", iast="ā", ipa="aː",
        category="svara_long", provenance="Yellappa Shastri 1953, Table 1 (p. 24)"
    ),
    3: AksharaEntry(
        number=3, primary_akshara="ಇ", variant_aksharas=["ಿ", "i"], vowel_matra="ಿ", iast="i", ipa="i",
        category="svara_short", provenance="Yellappa Shastri 1953, Table 1 (p. 24)"
    ),
    4: AksharaEntry(
        number=4, primary_akshara="ಈ", variant_aksharas=["ೀ", "ī"], vowel_matra="ೀ", iast="ī", ipa="iː",
        category="svara_long", provenance="Yellappa Shastri 1953, Table 1 (p. 24)"
    ),
    5: AksharaEntry(
        number=5, primary_akshara="ಉ", variant_aksharas=["ು", "u"], vowel_matra="ು", iast="u", ipa="u",
        category="svara_short", provenance="Yellappa Shastri 1953, Table 1 (p. 24)"
    ),
    6: AksharaEntry(
        number=6, primary_akshara="ಊ", variant_aksharas=["ೂ", "ū"], vowel_matra="ೂ", iast="ū", ipa="uː",
        category="svara_long", provenance="Yellappa Shastri 1953, Table 1 (p. 24)"
    ),
    7: AksharaEntry(
        number=7, primary_akshara="ಋ", variant_aksharas=["ೃ", "ṛ"], vowel_matra="ೃ", iast="ṛ", ipa="r̩",
        category="svara_vocalic", provenance="Yellappa Shastri 1953, Table 1 (p. 24)"
    ),
    8: AksharaEntry(
        number=8, primary_akshara="ೠ", variant_aksharas=["ೄ", "ṝ"], vowel_matra="ೄ", iast="ṝ", ipa="r̩ː",
        category="svara_vocalic_long", provenance="Yellappa Shastri 1953, Table 1 (p. 24)"
    ),
    9: AksharaEntry(
        number=9, primary_akshara="ಌ", variant_aksharas=["ḷ"], iast="ḷ", ipa="l̩",
        category="svara_vocalic", provenance="Yellappa Shastri 1953, Table 1 (p. 24)"
    ),
    10: AksharaEntry(
        number=10, primary_akshara="ೡ", variant_aksharas=["ḹ"], iast="ḹ", ipa="l̩ː",
        category="svara_vocalic_long", provenance="Yellappa Shastri 1953, Table 1 (p. 24)"
    ),
    11: AksharaEntry(
        number=11, primary_akshara="ಏ", variant_aksharas=["ಎ", "ೇ", "ೆ", "e", "ē"], vowel_matra="ೇ", iast="e", ipa="eː",
        category="svara_sandhyakshara", provenance="Yellappa Shastri 1953, Table 1 (p. 24)"
    ),
    12: AksharaEntry(
        number=12, primary_akshara="ಐ", variant_aksharas=["ೈ", "ai"], vowel_matra="ೈ", iast="ai", ipa="ai",
        category="svara_sandhyakshara", provenance="Yellappa Shastri 1953, Table 1 (p. 24)"
    ),
    13: AksharaEntry(
        number=13, primary_akshara="ಓ", variant_aksharas=["ಒ", "ೋ", "ೊ", "o", "ō"], vowel_matra="ೋ", iast="o", ipa="oː",
        category="svara_sandhyakshara", provenance="Yellappa Shastri 1953, Table 1 (p. 24)"
    ),
    14: AksharaEntry(
        number=14, primary_akshara="ಔ", variant_aksharas=["ೌ", "au"], vowel_matra="ೌ", iast="au", ipa="au",
        category="svara_sandhyakshara", provenance="Yellappa Shastri 1953, Table 1 (p. 24)"
    ),
    15: AksharaEntry(
        number=15, primary_akshara="ಅಂ", variant_aksharas=["ಂ", "ṃ", "am"], vowel_matra="ಂ", iast="aṃ", ipa="ʌm",
        category="yogavaha_anusvara", provenance="Yellappa Shastri 1953, Table 1 (p. 24)"
    ),
    16: AksharaEntry(
        number=16, primary_akshara="ಅಃ", variant_aksharas=["ಃ", "ḥ", "ah"], vowel_matra="ಃ", iast="aḥ", ipa="ʌh",
        category="yogavaha_visarga", provenance="Yellappa Shastri 1953, Table 1 (p. 24)"
    ),

    # 17-41: Vargiya Vyanjanas (25 Consonants)
    17: AksharaEntry(number=17, primary_akshara="ಕ", iast="ka", ipa="kʌ", category="kanthya", provenance="Yellappa Shastri 1953"),
    18: AksharaEntry(number=18, primary_akshara="ಖ", iast="kha", ipa="kʰʌ", category="kanthya", provenance="Yellappa Shastri 1953"),
    19: AksharaEntry(number=19, primary_akshara="ಗ", iast="ga", ipa="ɡʌ", category="kanthya", provenance="Yellappa Shastri 1953"),
    20: AksharaEntry(number=20, primary_akshara="ಘ", iast="gha", ipa="ɡʱʌ", category="kanthya", provenance="Yellappa Shastri 1953"),
    21: AksharaEntry(number=21, primary_akshara="ಙ", iast="ṅa", ipa="ŋʌ", category="kanthya_nasal", provenance="Yellappa Shastri 1953"),
    22: AksharaEntry(number=22, primary_akshara="ಚ", iast="ca", ipa="tʃʌ", category="talavya", provenance="Yellappa Shastri 1953"),
    23: AksharaEntry(number=23, primary_akshara="ಛ", iast="cha", ipa="tʃʰʌ", category="talavya", provenance="Yellappa Shastri 1953"),
    24: AksharaEntry(number=24, primary_akshara="ಜ", iast="ja", ipa="dʒʌ", category="talavya", provenance="Yellappa Shastri 1953"),
    25: AksharaEntry(number=25, primary_akshara="ಝ", iast="jha", ipa="dʒʱʌ", category="talavya", provenance="Yellappa Shastri 1953"),
    26: AksharaEntry(number=26, primary_akshara="ಞ", iast="ña", ipa="ɲʌ", category="talavya_nasal", provenance="Yellappa Shastri 1953"),
    27: AksharaEntry(number=27, primary_akshara="ಟ", iast="ṭa", ipa="ʈʌ", category="murdhanya", provenance="Yellappa Shastri 1953"),
    28: AksharaEntry(number=28, primary_akshara="ಠ", iast="ṭha", ipa="ʈʰʌ", category="murdhanya", provenance="Yellappa Shastri 1953"),
    29: AksharaEntry(number=29, primary_akshara="ಡ", iast="ḍa", ipa="ɖʌ", category="murdhanya", provenance="Yellappa Shastri 1953"),
    30: AksharaEntry(number=30, primary_akshara="ಢ", iast="ḍha", ipa="ɖʱʌ", category="murdhanya", provenance="Yellappa Shastri 1953"),
    31: AksharaEntry(number=31, primary_akshara="ಣ", iast="ṇa", ipa="ɳʌ", category="murdhanya_nasal", provenance="Yellappa Shastri 1953"),
    32: AksharaEntry(number=32, primary_akshara="ತ", iast="ta", ipa="t̪ʌ", category="dantya", provenance="Yellappa Shastri 1953"),
    33: AksharaEntry(number=33, primary_akshara="ಥ", iast="tha", ipa="t̪ʰʌ", category="dantya", provenance="Yellappa Shastri 1953"),
    34: AksharaEntry(number=34, primary_akshara="ದ", iast="da", ipa="d̪ʌ", category="dantya", provenance="Yellappa Shastri 1953"),
    35: AksharaEntry(number=35, primary_akshara="ಧ", iast="dha", ipa="d̪ʱʌ", category="dantya", provenance="Yellappa Shastri 1953"),
    36: AksharaEntry(number=36, primary_akshara="ನ", iast="na", ipa="n̪ʌ", category="dantya_nasal", provenance="Yellappa Shastri 1953"),
    37: AksharaEntry(number=37, primary_akshara="ಪ", iast="pa", ipa="pʌ", category="oshtya", provenance="Yellappa Shastri 1953"),
    38: AksharaEntry(number=38, primary_akshara="ಫ", iast="pha", ipa="pʰʌ", category="oshtya", provenance="Yellappa Shastri 1953"),
    39: AksharaEntry(number=39, primary_akshara="ಬ", iast="ba", ipa="bʌ", category="oshtya", provenance="Yellappa Shastri 1953"),
    40: AksharaEntry(number=40, primary_akshara="ಭ", iast="bha", ipa="bʱʌ", category="oshtya", provenance="Yellappa Shastri 1953"),
    41: AksharaEntry(number=41, primary_akshara="ಮ", iast="ma", ipa="mʌ", category="oshtya_nasal", provenance="Yellappa Shastri 1953"),

    # 42-50: Avargiya Vyanjanas (Semi-vowels, Sibilants, Aspirate)
    42: AksharaEntry(number=42, primary_akshara="ಯ", iast="ya", ipa="jʌ", category="antahastha", provenance="Yellappa Shastri 1953"),
    43: AksharaEntry(number=43, primary_akshara="ರ", iast="ra", ipa="rʌ", category="antahastha", provenance="Yellappa Shastri 1953"),
    44: AksharaEntry(number=44, primary_akshara="ಲ", iast="la", ipa="lʌ", category="antahastha", provenance="Yellappa Shastri 1953"),
    45: AksharaEntry(number=45, primary_akshara="ವ", iast="va", ipa="ʋʌ", category="antahastha", provenance="Yellappa Shastri 1953"),
    46: AksharaEntry(number=46, primary_akshara="ಶ", iast="śa", ipa="ʃʌ", category="ushman", provenance="Yellappa Shastri 1953"),
    47: AksharaEntry(number=47, primary_akshara="ಷ", iast="ṣa", ipa="ʂʌ", category="ushman", provenance="Yellappa Shastri 1953"),
    48: AksharaEntry(number=48, primary_akshara="ಸ", iast="sa", ipa="sʌ", category="ushman", provenance="Yellappa Shastri 1953"),
    49: AksharaEntry(number=49, primary_akshara="ಹ", iast="ha", ipa="hʌ", category="ushman", provenance="Yellappa Shastri 1953"),
    50: AksharaEntry(number=50, primary_akshara="ಳ", iast="ḷa", ipa="ɭʌ", category="drāviḍa_special", provenance="Yellappa Shastri 1953"),

    # 51-52: Archaic Halegannada Consonants (RRA and LLA)
    51: AksharaEntry(
        number=51, primary_akshara="ಱ", variant_aksharas=["ṟa", "RRA"], iast="ṟa", ipa="r̪ʌ",
        category="halegannada_rra", provenance="Kumudendu Muni, Siri Bhoovalaya (Old Kannada alveolar trill)"
    ),
    52: AksharaEntry(
        number=52, primary_akshara="ೞ", variant_aksharas=["ḻa", "LLA"], iast="ḻa", ipa="ɻʌ",
        category="halegannada_lla", provenance="Kumudendu Muni, Siri Bhoovalaya (Old Kannada retroflex central approximant)"
    ),

    # 53-54: Recognized Classical Conjuncts
    53: AksharaEntry(number=53, primary_akshara="ಕ್ಷ", variant_aksharas=["kṣa"], iast="kṣa", ipa="kʂʌ", category="samyukta", provenance="Yellappa Shastri 1953"),
    54: AksharaEntry(number=54, primary_akshara="ಜ್ಞ", variant_aksharas=["jña"], iast="jña", ipa="dʒɲʌ", category="samyukta", provenance="Yellappa Shastri 1953"),

    # 55-64: Auspicious Invocations, Prosodic Markers & Structural Symbols
    55: AksharaEntry(
        number=55, primary_akshara="ಶ್ರೀ", variant_aksharas=["śrī"], iast="śrī", ipa="ʃriː",
        category="mangala_shri", provenance="Siri Bhoovalaya opening invocations (Chakra 1)"
    ),
    56: AksharaEntry(
        number=56, primary_akshara="ಓಂ", variant_aksharas=["oṃ", "Aum"], iast="oṃ", ipa="oːm",
        category="pranava", provenance="Siri Bhoovalaya invocation"
    ),
    57: AksharaEntry(
        number=57, primary_akshara="್", variant_aksharas=["ತ್", "virāma", "halant"], iast="virāma", ipa="",
        category="structural_virama", provenance="Yellappa Shastri 1953", is_structural=True
    ),
    58: AksharaEntry(
        number=58, primary_akshara=" ", variant_aksharas=["ಯತಿ", "yati"], iast="yati", ipa="",
        category="caesura", provenance="Prosodic pause marker in Kanda meter", is_structural=True
    ),
    59: AksharaEntry(
        number=59, primary_akshara="", variant_aksharas=["ಪ್ರಾಸ", "prāsa"], iast="prāsa", ipa="",
        category="rhyme_marker", provenance="Siri Bhoovalaya prosodic rhyme index", is_structural=True
    ),
    60: AksharaEntry(
        number=60, primary_akshara="|", variant_aksharas=["।", "danda"], iast="|", ipa="",
        category="verse_danda_single", provenance="Verse half-line marker", is_structural=True
    ),
    61: AksharaEntry(
        number=61, primary_akshara="ಗ", variant_aksharas=["guru", "೨"], iast="guru", ipa="",
        category="chhandas_guru", provenance="Chhandas heavy syllabic weight (2 matras)"
    ),
    62: AksharaEntry(
        number=62, primary_akshara="ಲ", variant_aksharas=["laghu", "೧"], iast="laghu", ipa="",
        category="chhandas_laghu", provenance="Chhandas light syllabic weight (1 matra)"
    ),
    63: AksharaEntry(
        number=63, primary_akshara="||", variant_aksharas=["॥", "double_danda"], iast="||", ipa="",
        category="verse_danda_double", provenance="Stanza end marker", is_structural=True
    ),
    64: AksharaEntry(
        number=64, primary_akshara=" ", variant_aksharas=["ಶೂನ್ಯ", "space"], iast="śūnya", ipa="",
        category="shunya_space", provenance="Siri Bhoovalaya word/phrase delimiter", is_structural=True
    ),
}
