"""Synthetic PDF and fixture generator for deterministic engineering tests.

ALL DATA GENERATED HEREIN IS STRICTLY SYNTHETIC AND CLEARLY MARKED AS SUCH.
DO NOT USE THIS SYNTHETIC BENCHMARK TO MAKE CLAIMS ABOUT HISTORICAL MANUSCRIPT ACCURACY.
"""
from pathlib import Path
from typing import List, Optional
import fitz  # PyMuPDF

# Kannada Numerals: ೦=0, ೧=1, ೨=2, ೩=3, ೪=4, ೫=5, ೬=6, ೭=7, ೮=8, ೯=9
KANNADA_DIGITS = ["೦", "೧", "೨", "೩", "೪", "೫", "೬", "೭", "೮", "೯"]


def to_kannada_num(n: int) -> str:
    """Convert integer to Kannada numeral string."""
    return "".join(KANNADA_DIGITS[int(d)] for d in str(n))


def generate_synthetic_27x27_grid() -> List[List[str]]:
    """Generate a deterministic 27x27 grid with valid Siri Bhoovalaya domain numbers [1, 64]."""
    grid = []
    val = 1
    for r in range(27):
        row = []
        for c in range(27):
            num = (val % 64) + 1
            if (r + c) % 2 == 0:
                row.append(to_kannada_num(num))
            else:
                row.append(str(num))
            val += 1
        grid.append(row)
    return grid


def _find_kannada_font() -> Optional[fitz.Font]:
    """Locate an available Unicode font that supports Kannada."""
    candidate_paths = [
        r"C:\Windows\Fonts\Nirmala.ttc",
        r"C:\Windows\Fonts\NirmalaB.ttc",
        r"C:\Windows\Fonts\Tunga.ttf",
        "/usr/share/fonts/truetype/kannada/Kedage-n.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansKannada-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidate_paths:
        if Path(p).exists():
            try:
                return fitz.Font(fontfile=p)
            except Exception:
                pass
    return None


def generate_synthetic_pdf_bytes() -> bytes:
    """Generate a multi-page PDF containing:
    Page 1: 27x27 Numerical Matrix (clearly marked synthetic)
    Page 2: Halegannada Shlokas with dandas and verse markers
    Page 3: Historical commentary mentioning Kumudendu Muni, Siri Bhoovalaya, etc.
    """
    doc = fitz.open()
    k_font = _find_kannada_font()

    # --- PAGE 1: 27x27 Numerical Matrix ---
    p1 = doc.new_page(width=792, height=612)  # Landscape letter
    p1.insert_text((40, 30), "[SYNTHETIC TEST FIXTURE: 27x27 CHAKRA MATRIX]", fontsize=14)
    p1.insert_text((40, 48), "Synthetic 27x27 grid for engineering test suite validation.", fontsize=9)

    grid_data = generate_synthetic_27x27_grid()
    start_y = 70
    row_height = 19
    for r_idx, row in enumerate(grid_data):
        row_str = "  ".join(row)
        if k_font:
            tw = fitz.TextWriter(p1.rect)
            tw.append((40, start_y + (r_idx * row_height)), row_str, font=k_font, fontsize=8)
            tw.write_text(p1)
        else:
            p1.insert_text((40, start_y + (r_idx * row_height)), row_str, fontsize=8)

    # --- PAGE 2: Halegannada Shlokas ---
    p2 = doc.new_page(width=612, height=792)  # Portrait letter
    p2.insert_text((40, 40), "[SYNTHETIC TEST FIXTURE: HALEGANNADA SHLOKAS]", fontsize=14)
    p2.insert_text((40, 60), "Raw preserved verse with Halegannada markers and dandas:", fontsize=10)

    shloka_lines = [
        "ಶ್ರೀಮತ್ಪರಮ ಗಂಭೀರ ಸ್ಯಾದ್ವಾದಾಮೋಘ ಲಾಂಛನಂ |",
        "ಜೀಯಾತ್ ತ್ರೈಲೋಕ್ಯ ನಾಥಸ್ಯ ಶಾಸನಂ ಜಿನ ಶಾಸನಂ || ೧ ||",
        "",
        "ಒಳ್ಪು ಪೆಱತೊಂದಿಲ್ಲ ಕಂಡಪುದು ಜಿನೇಂದ್ರವಾಣಿ |",
        "ಅಂಕದಿಂ ಪೊಣರ್ಚಿದ ಸಿರಿಭೂವಲಯದೊಳ್ ಬೆಳಗುತಿರ್ಪುದು || ೨ ||",
    ]

    y_pos = 100
    for line in shloka_lines:
        if line:
            if k_font:
                tw = fitz.TextWriter(p2.rect)
                tw.append((50, y_pos), line, font=k_font, fontsize=11)
                tw.write_text(p2)
            else:
                p2.insert_text((50, y_pos), line, fontsize=11)
        y_pos += 26

    # --- PAGE 3: Historical Commentary & Hypothesis ---
    p3 = doc.new_page(width=612, height=792)
    p3.insert_text((40, 40), "[SYNTHETIC TEST FIXTURE: HISTORICAL COMMENTARY]", fontsize=14)

    commentary_paragraphs = [
        "This section discusses the historical context of Siri Bhoovalaya attributed to Kumudendu Muni.",
        "Kumudendu Muni composed the work using numerical Chakra matrices and Sarvatobhadra bandha.",
        "The text refers to ancient works including Shatkhandagama and teachings associated with Dharasena.",
        "Ankaphala maps numerals 1 to 64 to foundational phonemes across Kannada, Prakrit, and Sanskrit.",
        "Hypothesis note: A modern claim hypothesizes that the matrix encodes 718 languages through permutations.",
    ]

    y_pos = 90
    for para in commentary_paragraphs:
        p3.insert_text((40, y_pos), para, fontsize=10)
        y_pos += 30

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes
