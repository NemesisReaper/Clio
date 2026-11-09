"""Gomutrika Bandha (ಗೋಮೂತ್ರಿಕಾ ಬಂಧ) - Zigzag Wave Traversal.

Mathematical Rules:
"Gomutrika" ("in the manner of a cow's zigzag gait"):
A periodic wave trajectory alternating between paired adjacent rows:
r(c) = base_row + (c % 2) for c in [0..26].

Phase 1 (Forward Crest):
  (r, 0) -> (r+1, 1) -> (r, 2) -> (r+1, 3) -> ... -> (r, 26)

Phase 2 (Return Trough / Inverted Wave):
  (r+1, 26) -> (r, 25) -> (r+1, 24) -> (r, 23) -> ... -> (r+1, 0)

Progression:
Advances sequentially through row pairs base_row in {0, 2, 4, ..., 24}.
Total steps for full matrix coverage: 27 x 27.
"""
from typing import Any, Dict, List, Optional, Tuple

from clio.models.decipherment import BandhaPattern
from clio.decipherment.bandhas.base import (
    BandhaMetadata,
    BaseBandha,
    TraversalDirection,
)


class GomutrikaBandha(BaseBandha):
    """Gomutrika (Alternating Zigzag Wave) Traversal Generator."""

    def __init__(self):
        meta = BandhaMetadata(
            name=BandhaPattern.GOMUTRIKA,
            kannada_name="ಗೋಮೂತ್ರಿಕಾ ಬಂಧ",
            description="Alternating zigzag wave trajectory oscillating between adjacent rows with period 2.",
            mathematical_rules=(
                "Oscillating wave r(c) = base_row + (c % 2) across column span c in [0..26], "
                "followed by inverted return r(c) = base_row + 1 - (c % 2). "
                "Advances row pairs base_row += 2 across the 27x27 grid."
            ),
            typical_length=729,
            symmetry_order=2,
            historical_source="Dandin, Kavyadarsha III.63-65 & Kumudendu Muni, Siri Bhoovalaya.",
        )
        super().__init__(meta)

    def generate_steps(
        self,
        start_coord: Tuple[int, int] = (0, 0),
        max_steps: int = 729,
        direction: TraversalDirection = TraversalDirection.FORWARD,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[int, int]]:
        params = params or {}
        coords: List[Tuple[int, int]] = []
        orientation = params.get("orientation", "HORIZONTAL")

        if orientation == "VERTICAL":
            return self._generate_vertical(max_steps)

        # Horizontal zigzag across row pairs (0,1), (2,3), ..., (24,25), and final row 26
        for base_row in range(0, 26, 2):
            # Phase 1: Forward wave
            for c in range(27):
                r = base_row + (c % 2)
                if r <= 26:
                    coords.append((r, c))
                if len(coords) >= max_steps:
                    return coords

            # Phase 2: Inverted return wave along the same pair
            for c in range(26, -1, -1):
                r = base_row + (1 - (c % 2))
                if r <= 26:
                    coords.append((r, c))
                if len(coords) >= max_steps:
                    return coords

        # Final row 26 if remaining steps
        if len(coords) < max_steps:
            for c in range(27):
                coords.append((26, c))
                if len(coords) >= max_steps:
                    return coords

        return coords[:max_steps]

    def _generate_vertical(self, max_steps: int) -> List[Tuple[int, int]]:
        """Vertical column-pair oscillating wave."""
        coords: List[Tuple[int, int]] = []
        for base_col in range(0, 26, 2):
            for r in range(27):
                c = base_col + (r % 2)
                if c <= 26:
                    coords.append((r, c))
                if len(coords) >= max_steps:
                    return coords

            for r in range(26, -1, -1):
                c = base_col + (1 - (r % 2))
                if c <= 26:
                    coords.append((r, c))
                if len(coords) >= max_steps:
                    return coords

        return coords[:max_steps]
