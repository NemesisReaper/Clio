"""Sarvatobhadra Bandha (ಸರ್ವತೋಭದ್ರ ಬಂಧ) - Omnidirectional Symmetrical Traversal.

Mathematical Rules:
"Sarvatah" (from all sides) + "Bhadra" (good/propitious).
In Siri Bhoovalaya, Sarvatobhadra embodies 4-fold or 8-fold planar reflection symmetry:
f(r, c) == f(26 - r, c) == f(r, 26 - c) == f(26 - r, 26 - c)

Supported Traversal Modes:
1. CONCENTRIC_SPIRAL (Default): Inward concentric perimeter frames k = 0..13.
   For each frame k:
   - Top edge: (k, k) -> (k, 26-k)
   - Right edge: (k+1, 26-k) -> (26-k, 26-k)
   - Bottom edge: (26-k, 25-k) -> (26-k, k)
   - Left edge: (25-k, k) -> (k+1, k)
   Total cells covered: exactly 729 cells without omission or duplication.

2. SERPENTINE_SYMMETRIC: Boustrophedon raster preserving row-pair reflection.
   - For even row r: (r, 0) -> (r, 26)
   - For odd row r: (r, 26) -> (r, 0)

3. RADIAL_OUTWARD: Expands from central seed (13, 13) outwards in concentric square rings.
"""
from typing import Any, Dict, List, Optional, Tuple

from clio.models.decipherment import BandhaPattern
from clio.decipherment.bandhas.base import (
    BandhaMetadata,
    BaseBandha,
    TraversalDirection,
)


class SarvatobhadraBandha(BaseBandha):
    """Sarvatobhadra Traversal Generator."""

    def __init__(self):
        meta = BandhaMetadata(
            name=BandhaPattern.SARVATOBHADRA,
            kannada_name="ಸರ್ವತೋಭದ್ರ ಬಂಧ",
            description="Omnidirectional 4-fold symmetric matrix traversal across 27x27 grid.",
            mathematical_rules=(
                "Concentric inward perimeter rings k in [0..13] or boustrophedon with "
                "reflection invariance f(r, c) == f(26-r, 26-c). Complete coverage of 729 cells."
            ),
            typical_length=729,
            symmetry_order=4,
            historical_source="Siri Bhoovalaya Chapter 1, Kumudendu Muni (c. 800-850 CE).",
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
        mode = params.get("mode", "CONCENTRIC_SPIRAL")

        if mode == "SERPENTINE_SYMMETRIC":
            return self._generate_serpentine(max_steps)
        elif mode == "RADIAL_OUTWARD":
            return self._generate_radial_outward(max_steps)
        else:
            return self._generate_concentric_spiral(max_steps)

    def _generate_concentric_spiral(self, max_steps: int) -> List[Tuple[int, int]]:
        """Traverse concentric frames from outer edge k=0 down to center k=13."""
        coords: List[Tuple[int, int]] = []
        n = 27

        for k in range(14):  # 0 to 13 (27 // 2 = 13, center is k=13)
            # Top edge: (k, k) to (k, n - 1 - k)
            for c in range(k, n - k):
                coords.append((k, c))
                if len(coords) >= max_steps:
                    return coords

            # Right edge: (k + 1, n - 1 - k) to (n - 1 - k, n - 1 - k)
            for r in range(k + 1, n - k):
                coords.append((r, n - 1 - k))
                if len(coords) >= max_steps:
                    return coords

            # Bottom edge: (n - 1 - k, n - 2 - k) down to (n - 1 - k, k)
            for c in range(n - 2 - k, k - 1, -1):
                coords.append((n - 1 - k, c))
                if len(coords) >= max_steps:
                    return coords

            # Left edge: (n - 2 - k, k) down to (k + 1, k)
            for r in range(n - 2 - k, k, -1):
                coords.append((r, k))
                if len(coords) >= max_steps:
                    return coords

        return coords

    def _generate_serpentine(self, max_steps: int) -> List[Tuple[int, int]]:
        """Serpentine row-by-row boustrophedon traversal."""
        coords: List[Tuple[int, int]] = []
        for r in range(27):
            if r % 2 == 0:
                for c in range(27):
                    coords.append((r, c))
                    if len(coords) >= max_steps:
                        return coords
            else:
                for c in range(26, -1, -1):
                    coords.append((r, c))
                    if len(coords) >= max_steps:
                        return coords
        return coords

    def _generate_radial_outward(self, max_steps: int) -> List[Tuple[int, int]]:
        """Start from center (13, 13) and expand outwards in square orbits."""
        coords: List[Tuple[int, int]] = [(13, 13)]
        center = 13

        for radius in range(1, 14):
            # Top edge of square orbit: row = center - radius, col from center-radius to center+radius
            r_top = center - radius
            r_bot = center + radius
            c_left = center - radius
            c_right = center + radius

            for c in range(c_left, c_right + 1):
                coords.append((r_top, c))
            for r in range(r_top + 1, r_bot + 1):
                coords.append((r, c_right))
            for c in range(c_right - 1, c_left - 1, -1):
                coords.append((r_bot, c))
            for r in range(r_bot - 1, r_top, -1):
                coords.append((r, c_left))

            if len(coords) >= max_steps:
                return coords[:max_steps]

        return coords[:max_steps]
