"""Historically documented Ankaphala (numerical-to-akshara) mapping tables.

Sources & Critical Provenance:
1. "Siri Bhoovalaya of Kumudendu Muni", Part 1.
   Edited by K. Yellappa Shastri & Karlamangalam Srikantaiah.
   Published by Central Jain Board (ಕೇಂದ್ರ ಜೈನ ಬೋರ್ಡ್), Bangalore, 1953.
   Table 1 (p. 24): 64-Akshara Canonical Lipi.
2. Classical 64-Akshara Jain Canonical Lipi tradition (Samavayanga Sutra).

Historical Provenance Audit:
- Directly documented in 1953 Bangalore publication by Yellappa Shastri.
- Ancient 9th-century authorship of this exact numerical assignment is contested
  among 20th-century scholars (e.g. Prof. M. V. Seetha Ramiah, Dr. M. Chidananda Murthy).
- Therefore, tagged with RuleVerificationState.PARTIALLY_VERIFIED.
- The raw historical table is strictly preserved independently from any normalized
  or ligature-composed lookup representation.
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from clio.models.provenance import RuleVerificationState


class AnkaphalaVersion(str, Enum):
    V1_YELLAPPA_SHASTRI_1953 = "v1_yellappa_shastri_1953"
    V2_PHONETIC_VARIANTS = "v2_phonetic_variants"


class RawAksharaEntry(BaseModel):
    """Raw, unmodified historical grapheme entry as printed in the 1953 edition.
    
    Contains strictly the literal character printed in the source table without
    matra substitution, romanization variants, or ligature composition rules.
    """
    number: int = Field(..., ge=1, le=64)
    raw_grapheme: str
    historical_name: str
    category: str
    is_archaic: bool = False
    is_structural: bool = False
    source_citation: str = "Yellappa Shastri (1953), Table 1, p. 24"


class AksharaEntry(BaseModel):
    """Derived normalized lookup representation for computational alignment and analysis."""
    number: int = Field(..., ge=1, le=64)
    primary_akshara: str
    variant_aksharas: List[str] = Field(default_factory=list)
    vowel_matra: Optional[str] = None
    iast: str
    ipa: str
    category: str
    provenance: str
    is_structural: bool = False
    verification_state: RuleVerificationState = RuleVerificationState.PARTIALLY_VERIFIED


class TableProvenanceMetadata(BaseModel):
    """Provenance and audit metadata for an Ankaphala table version."""
    table_version: str
    title: str
    editors: str
    publisher: str
    publication_year: int
    page_reference: str
    verification_state: RuleVerificationState
    total_symbols: int = 64
    has_archaic_characters: bool = True
    archaic_characters: Dict[int, str] = Field(default_factory=dict)
    has_algorithmic_normalization: bool = False
    audit_notes: str


TABLE_V1_PROVENANCE_AUDIT = TableProvenanceMetadata(
    table_version=AnkaphalaVersion.V1_YELLAPPA_SHASTRI_1953.value,
    title="Siri Bhoovalaya (Part 1) — 64-Akshara Ankaphala Key",
    editors="K. Yellappa Shastri & Karlamangalam Srikantaiah",
    publisher="Central Jain Board, Bangalore",
    publication_year=1953,
    page_reference="Chapter 1, Table 1, p. 24",
    verification_state=RuleVerificationState.PARTIALLY_VERIFIED,
    total_symbols=64,
    has_archaic_characters=True,
    archaic_characters={
        51: "ಱ (Old Kannada alveolar trill, RRA)",
        52: "ೞ (Old Kannada retroflex central approximant, LLA/ZHA)",
    },
    has_algorithmic_normalization=False,
    audit_notes=(
        "The 1-to-64 symbol mapping is directly documented in the 1953 publication. "
        "However, whether Kumudendu Muni (c. 850 CE) personally authored this exact table "
        "or whether it was reconstructed by Yellappa Shastri from palm-leaf marginalia "
        "remains an open scholarly question. Tagged as PARTIALLY_VERIFIED."
    ),
)


# ============================================================================
# 1. RAW HISTORICAL TABLE (Strictly Literal & Uncomposed)
# ============================================================================
RAW_HISTORICAL_ANKAPHALA_V1: Dict[int, RawAksharaEntry] = {
    # 1-16: Svaras and Yogavahas
    1: RawAksharaEntry(number=1, raw_grapheme="ಅ", historical_name="Hrasva A", category="svara"),
    2: RawAksharaEntry(number=2, raw_grapheme="ಆ", historical_name="Dirgha AA", category="svara"),
    3: RawAksharaEntry(number=3, raw_grapheme="ಇ", historical_name="Hrasva I", category="svara"),
    4: RawAksharaEntry(number=4, raw_grapheme="ಈ", historical_name="Dirgha II", category="svara"),
    5: RawAksharaEntry(number=5, raw_grapheme="ಉ", historical_name="Hrasva U", category="svara"),
    6: RawAksharaEntry(number=6, raw_grapheme="ಊ", historical_name="Dirgha UU", category="svara"),
    7: RawAksharaEntry(number=7, raw_grapheme="ಋ", historical_name="Vocalic R", category="svara"),
    8: RawAksharaEntry(number=8, raw_grapheme="ೠ", historical_name="Vocalic RR", category="svara"),
    9: RawAksharaEntry(number=9, raw_grapheme="ಌ", historical_name="Vocalic L", category="svara"),
    10: RawAksharaEntry(number=10, raw_grapheme="ೡ", historical_name="Vocalic LL", category="svara"),
    11: RawAksharaEntry(number=11, raw_grapheme="ಏ", historical_name="Dirgha E", category="svara"),
    12: RawAksharaEntry(number=12, raw_grapheme="ಐ", historical_name="Sandhyakshara AI", category="svara"),
    13: RawAksharaEntry(number=13, raw_grapheme="ಓ", historical_name="Dirgha O", category="svara"),
    14: RawAksharaEntry(number=14, raw_grapheme="ಔ", historical_name="Sandhyakshara AU", category="svara"),
    15: RawAksharaEntry(number=15, raw_grapheme="ಅಂ", historical_name="Anusvara AM", category="yogavaha"),
    16: RawAksharaEntry(number=16, raw_grapheme="ಅಃ", historical_name="Visarga AH", category="yogavaha"),

    # 17-41: Vargiya Vyanjanas (25 Consonants)
    17: RawAksharaEntry(number=17, raw_grapheme="ಕ", historical_name="Ka", category="vargiya"),
    18: RawAksharaEntry(number=18, raw_grapheme="ಖ", historical_name="Kha", category="vargiya"),
    19: RawAksharaEntry(number=19, raw_grapheme="ಗ", historical_name="Ga", category="vargiya"),
    20: RawAksharaEntry(number=20, raw_grapheme="ಘ", historical_name="Gha", category="vargiya"),
    21: RawAksharaEntry(number=21, raw_grapheme="ಙ", historical_name="Nga", category="vargiya"),
    22: RawAksharaEntry(number=22, raw_grapheme="ಚ", historical_name="Ca", category="vargiya"),
    23: RawAksharaEntry(number=23, raw_grapheme="ಛ", historical_name="Cha", category="vargiya"),
    24: RawAksharaEntry(number=24, raw_grapheme="ಜ", historical_name="Ja", category="vargiya"),
    25: RawAksharaEntry(number=25, raw_grapheme="ಝ", historical_name="Jha", category="vargiya"),
    26: RawAksharaEntry(number=26, raw_grapheme="ಞ", historical_name="Nya", category="vargiya"),
    27: RawAksharaEntry(number=27, raw_grapheme="ಟ", historical_name="Tta", category="vargiya"),
    28: RawAksharaEntry(number=28, raw_grapheme="ಠ", historical_name="Ttha", category="vargiya"),
    29: RawAksharaEntry(number=29, raw_grapheme="ಡ", historical_name="Dda", category="vargiya"),
    30: RawAksharaEntry(number=30, raw_grapheme="ಢ", historical_name="Ddha", category="vargiya"),
    31: RawAksharaEntry(number=31, raw_grapheme="ಣ", historical_name="Nna", category="vargiya"),
    32: RawAksharaEntry(number=32, raw_grapheme="ತ", historical_name="Ta", category="vargiya"),
    33: RawAksharaEntry(number=33, raw_grapheme="ಥ", historical_name="Tha", category="vargiya"),
    34: RawAksharaEntry(number=34, raw_grapheme="ದ", historical_name="Da", category="vargiya"),
    35: RawAksharaEntry(number=35, raw_grapheme="ಧ", historical_name="Dha", category="vargiya"),
    36: RawAksharaEntry(number=36, raw_grapheme="ನ", historical_name="Na", category="vargiya"),
    37: RawAksharaEntry(number=37, raw_grapheme="ಪ", historical_name="Pa", category="vargiya"),
    38: RawAksharaEntry(number=38, raw_grapheme="ಫ", historical_name="Pha", category="vargiya"),
    39: RawAksharaEntry(number=39, raw_grapheme="ಬ", historical_name="Ba", category="vargiya"),
    40: RawAksharaEntry(number=40, raw_grapheme="ಭ", historical_name="Bha", category="vargiya"),
    41: RawAksharaEntry(number=41, raw_grapheme="ಮ", historical_name="Ma", category="vargiya"),

    # 42-50: Avargiya Vyanjanas
    42: RawAksharaEntry(number=42, raw_grapheme="ಯ", historical_name="Ya", category="avargiya"),
    43: RawAksharaEntry(number=43, raw_grapheme="ರ", historical_name="Ra", category="avargiya"),
    44: RawAksharaEntry(number=44, raw_grapheme="ಲ", historical_name="La", category="avargiya"),
    45: RawAksharaEntry(number=45, raw_grapheme="ವ", historical_name="Va", category="avargiya"),
    46: RawAksharaEntry(number=46, raw_grapheme="ಶ", historical_name="Sha (Palatal)", category="avargiya"),
    47: RawAksharaEntry(number=47, raw_grapheme="ಷ", historical_name="Ssa (Retroflex)", category="avargiya"),
    48: RawAksharaEntry(number=48, raw_grapheme="ಸ", historical_name="Sa (Dental)", category="avargiya"),
    49: RawAksharaEntry(number=49, raw_grapheme="ಹ", historical_name="Ha", category="avargiya"),
    50: RawAksharaEntry(number=50, raw_grapheme="ಳ", historical_name="Lla", category="avargiya"),

    # 51-52: Archaic Halegannada Consonants
    51: RawAksharaEntry(number=51, raw_grapheme="ಱ", historical_name="Rra (Old Kannada alveolar trill)", category="archaic", is_archaic=True),
    52: RawAksharaEntry(number=52, raw_grapheme="ೞ", historical_name="Zha (Old Kannada retroflex approximant)", category="archaic", is_archaic=True),

    # 53-54: Classical Recognized Conjuncts
    53: RawAksharaEntry(number=53, raw_grapheme="ಕ್ಷ", historical_name="Kssa Conjunct", category="samyukta"),
    54: RawAksharaEntry(number=54, raw_grapheme="ಜ್ಞ", historical_name="Jnya Conjunct", category="samyukta"),

    # 55-64: Invocations, Prosodic Markers & Structural Symbols
    55: RawAksharaEntry(number=55, raw_grapheme="ಶ್ರೀ", historical_name="Mangala Shri", category="invocation"),
    56: RawAksharaEntry(number=56, raw_grapheme="ಓಂ", historical_name="Pranava Om", category="invocation"),
    57: RawAksharaEntry(number=57, raw_grapheme="್", historical_name="Virama / Halant", category="structural", is_structural=True),
    58: RawAksharaEntry(number=58, raw_grapheme=" ", historical_name="Yati (Prosodic Caesura)", category="structural", is_structural=True),
    59: RawAksharaEntry(number=59, raw_grapheme="", historical_name="Prasa (Rhyme Index)", category="structural", is_structural=True),
    60: RawAksharaEntry(number=60, raw_grapheme="|", historical_name="Single Danda (Half-verse)", category="structural", is_structural=True),
    61: RawAksharaEntry(number=61, raw_grapheme="ಗ", historical_name="Guru Syllabic Marker", category="chhandas"),
    62: RawAksharaEntry(number=62, raw_grapheme="ಲ", historical_name="Laghu Syllabic Marker", category="chhandas"),
    63: RawAksharaEntry(number=63, raw_grapheme="||", historical_name="Double Danda (Stanza End)", category="structural", is_structural=True),
    64: RawAksharaEntry(number=64, raw_grapheme=" ", historical_name="Shunya (Phrase Delimiter)", category="structural", is_structural=True),
}


# ============================================================================
# 2. DERIVED NORMALIZED TABLE (With Matra and Phonetic Extensions)
# ============================================================================
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
    64: RawAksharaEntry(number=64, raw_grapheme=" ", historical_name="Shunya (Phrase Delimiter)", category="structural", is_structural=True)
    if False else AksharaEntry(
        number=64, primary_akshara=" ", variant_aksharas=["ಶೂನ್ಯ", "space"], iast="śūnya", ipa="",
        category="shunya_space", provenance="Siri Bhoovalaya word/phrase delimiter", is_structural=True
    ),
}
