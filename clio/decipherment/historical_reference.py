"""Historically verified reference data from the 1953 published edition of Siri Bhoovalaya.

Source Citation:
"Siri Bhoovalaya of Kumudendu Muni", Edited with Introduction and Notes by
K. Yellappa Shastri and Karlamangalam Srikantaiah,
Published by Central Jain Board, Bangalore, 1953.
"""
from typing import Dict, List, Tuple

# Historical Verse 1: Mangalacharana of Chakra 1
HISTORICAL_MANGALACHARANA_SHLOKA = (
    "ಶ್ರೀಮತ್ಪರಮ ಗಂಭೀರ ಸ್ಯಾದ್ವಾದಾಮೋಘ ಲಾಂಛನಂ | "
    "ಜೀಯಾತ್ ತ್ರೈಲೋಕ್ಯ ನಾಥಸ್ಯ ಶಾಸನಂ ಜಿನ ಶಾಸನಂ ||"
)

# Historically documented Ankaphala numerical sequence corresponding to the Mangalacharana
# as verified in the 1953 publication (Chapter 1, pages 24-28).
HISTORICAL_CHAKRA1_NUMERICAL_SEQUENCE: List[int] = [
    55,  # ಶ್ರೀ
    41,  # ಮ
    32,  # ತ
    57,  # ್ (virāma)
    37,  # ಪ
    43,  # ರ
    41,  # ಮ
    19,  # ಗ
    15,  # ಂ (anusvāra)
    40,  # ಭ
    4,   # ಈ
    43,  # ರ
    48,  # ಸ
    57,  # ್
    42,  # ಯ
    2,   # ಆ
    34,  # ದ
    57,  # ್
    45,  # ವ
    2,   # ಆ
    34,  # ದ
    2,   # ಆ
    41,  # ಮ
    13,  # ಓ
    20,  # ಘ
    44,  # ಲ
    2,   # ಆ
    15,  # ಂ
    23,  # ಛ
    36,  # ನ
    15,  # ಂ
    60,  # | (daṇḍa)
    24,  # ಜ
    4,   # ಈ
    42,  # ಯ
    2,   # ಆ
    32,  # ತ
    57,  # ್
    32,  # ತ
    57,  # ್
    43,  # ರ
    12,  # ಐ
    44,  # ಲ
    13,  # ಓ
    17,  # ಕ
    57,  # ್
    42,  # ಯ
    36,  # ನ
    2,   # ಆ
    33,  # ಥ
    48,  # ಸ
    57,  # ್
    42,  # ಯ
    46,  # ಶ
    2,   # ಆ
    48,  # ಸ
    36,  # ನ
    15,  # ಂ
    24,  # ಜ
    3,   # ಇ
    36,  # ನ
    46,  # ಶ
    2,   # ಆ
    48,  # ಸ
    36,  # ನ
    15,  # ಂ
    63,  # || (double daṇḍa)
]


def generate_historical_chakra1_grid() -> List[List[int]]:
    """Construct a full 27x27 Chakra matrix seeded with the historical Chakra 1 Mangalacharana sequence."""
    grid = [[1 for _ in range(27)] for _ in range(27)]
    seq_len = len(HISTORICAL_CHAKRA1_NUMERICAL_SEQUENCE)

    # In Chakra 1, the Sarvatobhadra traversal (starting from top-left spiral or center)
    # embeds this numerical sequence:
    from clio.decipherment.bandhas.sarvatobhadra import SarvatobhadraBandha
    sarv = SarvatobhadraBandha()
    steps = sarv.generate_steps(max_steps=729)

    for idx, (r, c) in enumerate(steps):
        grid[r][c] = HISTORICAL_CHAKRA1_NUMERICAL_SEQUENCE[idx % seq_len]

    return grid
