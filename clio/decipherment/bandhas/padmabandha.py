"""Padmabandha (ಪದ್ಮಬಂಧ) - Lotus Traversal Generator.

Mathematical Rules:
The Lotus consists of:
1. Karnika (pericarp / core): Center cell (13, 13).
2. Ashta-Dala (8 Petals): Rays emanating at angular multiples of 45 degrees:
   Directions:
   d0: North     (dr = -1, dc =  0)
   d1: NorthEast (dr = -1, dc = +1)
   d2: East      (dr =  0, dc = +1)
   d3: SouthEast (dr = +1, dc = +1)
   d4: South     (dr = +1, dc =  0)
   d5: SouthWest (dr = +1, dc = -1)
   d6: West      (dr =  0, dc = -1)
   d7: NorthWest (dr = -1, dc = -1)

Petal Loop Generation:
For each petal i in 0..7:
  - Emanate from core (13, 13) outwards along spoke d_i up to radius R
  - Arc lateral connection to spoke d_{(i+1)%8}
  - Inward return along spoke d_{(i+1)%8} back to core (13, 13)

This matches the classical Sanskrit & Halegannada Ashtadala Padmabandha verse structure
described in Kavyadarsha and Kumudendu's Siri Bhoovalaya.
"""
from typing import Any, Dict, List, Optional, Tuple

from clio.models.decipherment import BandhaPattern
from clio.models.provenance import DocumentationLevel, RuleVerificationState
from clio.decipherment.bandhas.base import (
    BandhaMetadata,
    BaseBandha,
    TraversalDirection,
)


class Padmabandha(BaseBandha):
    """Padmabandha (8-Petal and 16-Petal Lotus) Traversal Generator."""

    DIRECTIONS_8 = [
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
            name=BandhaPattern.PADMABANDHA,
            kannada_name="ಪದ್ಮಬಂಧ",
            description="8-petal (Ashtadala) concentric lotus petal loop traversal radiating from center (13, 13).",
            mathematical_rules=(
                "Center karnika at (13, 13). 8 petals at 45-degree angular steps. "
                "Each petal loops outward from center along spoke i to radius R, "
                "arcs to spoke (i+1)%8, and returns inwards to center."
            ),
            typical_length=64,
            symmetry_order=8,
            historical_source="Kumudendu Muni, Siri Bhoovalaya & Dandin, Kavyadarsha (III.41-43).",
            verification_state=RuleVerificationState.PARTIALLY_VERIFIED,
            documentation_level=DocumentationLevel.INFERRED,
            provenance_rule_id="RULE_BANDHA_PADMABANDHA_8PETAL",
            authenticity_disclaimer=(
                "The 8-petal lotus structure is classical poetics canon (Kavyadarsha III.41-43). "
                "The discrete coordinate sequence across 27x27 grid coordinates is a computational discretization."
            ),
        )
        super().__init__(meta)

    def generate_steps(
        self,
        start_coord: Tuple[int, int] = (13, 13),
        max_steps: int = 729,
        direction: TraversalDirection = TraversalDirection.FORWARD,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[int, int]]:
        params = params or {}
        cr, cc = start_coord
        radius = int(params.get("radius", 6))
        # Ensure radius stays within grid from center
        radius = min(max(radius, 2), 12)

        coords: List[Tuple[int, int]] = []
        # Center cell is initial core
        coords.append((cr, cc))

        # Traverse 8 petals
        for p_idx in range(8):
            dr1, dc1 = self.DIRECTIONS_8[p_idx]
            dr2, dc2 = self.DIRECTIONS_8[(p_idx + 1) % 8]

            # Outward along spoke 1
            for step in range(1, radius + 1):
                r = cr + (dr1 * step)
                c = cc + (dc1 * step)
                if 0 <= r <= 26 and 0 <= c <= 26:
                    coords.append((r, c))
                if len(coords) >= max_steps:
                    return coords

            # Inward along adjacent spoke 2
            for step in range(radius, 0, -1):
                r = cr + (dr2 * step)
                c = cc + (dc2 * step)
                if 0 <= r <= 26 and 0 <= c <= 26:
                    coords.append((r, c))
                if len(coords) >= max_steps:
                    return coords

            # Return to center
            coords.append((cr, cc))
            if len(coords) >= max_steps:
                return coords

        # If more steps requested, expand to secondary larger radii
        current_rad = radius + 2
        while len(coords) < max_steps and current_rad <= 12:
            for p_idx in range(8):
                dr1, dc1 = self.DIRECTIONS_8[p_idx]
                dr2, dc2 = self.DIRECTIONS_8[(p_idx + 1) % 8]

                for step in range(1, current_rad + 1):
                    r = cr + (dr1 * step)
                    c = cc + (dc1 * step)
                    if 0 <= r <= 26 and 0 <= c <= 26:
                        coords.append((r, c))
                    if len(coords) >= max_steps:
                        return coords

                for step in range(current_rad, 0, -1):
                    r = cr + (dr2 * step)
                    c = cc + (dc2 * step)
                    if 0 <= r <= 26 and 0 <= c <= 26:
                        coords.append((r, c))
                    if len(coords) >= max_steps:
                        return coords

                coords.append((cr, cc))
                if len(coords) >= max_steps:
                    return coords
            current_rad += 2

        return coords[:max_steps]

