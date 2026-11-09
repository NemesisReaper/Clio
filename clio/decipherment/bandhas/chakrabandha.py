"""Chakrabandha (ಚಕ್ರಬಂಧ) - Concentric Wheel and Spoke Traversal.

Mathematical Rules:
A wheel-form Chitra-Kavya layout consisting of:
1. Hub (Nabhi): Center cell at (13, 13).
2. Spokes (Ara): 8 radial axes at 0, 45, 90, 135, 180, 225, 270, 315 degrees.
3. Rims (Nemi): Concentric rings at radii R in {2, 4, 6, 8, 10, 12}.

Traversal alternates between radial spoke progression and concentric rim revolutions.
"""
from typing import Any, Dict, List, Optional, Tuple

from clio.models.decipherment import BandhaPattern
from clio.decipherment.bandhas.base import (
    BandhaMetadata,
    BaseBandha,
    TraversalDirection,
)


class Chakrabandha(BaseBandha):
    """Chakrabandha (Wheel & Spokes) Traversal Generator."""

    SPOKES_8 = [
        (-1, 0),   # N
        (-1, 1),   # NE
        (0, 1),    # E
        (1, 1),    # SE
        (1, 0),    # S
        (1, -1),   # SW
        (0, -1),   # W
        (-1, -1),  # NW
    ]

    def __init__(self):
        meta = BandhaMetadata(
            name=BandhaPattern.CHAKRABANDHA,
            kannada_name="ಚಕ್ರಬಂಧ",
            description="Concentric wheel traversal with central hub (13, 13), 8 radial spokes, and circular rims.",
            mathematical_rules=(
                "Hub at (13, 13). For concentric radii R in [2, 4, 6, 8, 10, 12]: "
                "radiates out along spoke k, traverses perimeter rim arc to spoke (k+1)%8, "
                "and returns to hub, followed by complete circular rim scan."
            ),
            typical_length=729,
            symmetry_order=8,
            historical_source="Kumudendu Muni, Siri Bhoovalaya & Agnipurana Chitra-Kavya chapters.",
        )
        super().__init__(meta)

    def generate_steps(
        self,
        start_coord: Tuple[int, int] = (13, 13),
        max_steps: int = 729,
        direction: TraversalDirection = TraversalDirection.FORWARD,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[int, int]]:
        coords: List[Tuple[int, int]] = []
        cr, cc = start_coord
        coords.append((cr, cc))

        for r_val in [2, 4, 6, 8, 10, 12]:
            # 1. Spoke traversal
            for dr, dc in self.SPOKES_8:
                for step in range(1, r_val + 1):
                    r = cr + (dr * step)
                    c = cc + (dc * step)
                    if 0 <= r <= 26 and 0 <= c <= 26:
                        coords.append((r, c))
                    if len(coords) >= max_steps:
                        return coords

            # 2. Perimeter rim square scan at this radius
            top = max(0, cr - r_val)
            bot = min(26, cr + r_val)
            left = max(0, cc - r_val)
            right = min(26, cc + r_val)

            for c in range(left, right + 1):
                coords.append((top, c))
            for r in range(top + 1, bot + 1):
                coords.append((r, right))
            for c in range(right - 1, left - 1, -1):
                coords.append((bot, c))
            for r in range(bot - 1, top, -1):
                coords.append((r, left))

            if len(coords) >= max_steps:
                return coords[:max_steps]

        return coords[:max_steps]
