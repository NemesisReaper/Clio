"""Base Bandha abstract class and trajectory validation utilities.

Each Bandha implements a rigorous geometric or poetic traversal across a 27x27 matrix,
validating coordinate bounds, duplicate steps, and traversal direction.
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from clio.models.decipherment import (
    BandhaPattern,
    CoordinateStep,
    TraversalTrajectory,
)
from clio.models.provenance import DocumentationLevel, RuleVerificationState


class TraversalDirection(str, Enum):
    FORWARD = "FORWARD"
    REVERSE = "REVERSE"
    CLOCKWISE = "CLOCKWISE"
    COUNTER_CLOCKWISE = "COUNTER_CLOCKWISE"
    BIDIRECTIONAL = "BIDIRECTIONAL"


class BandhaMetadata(BaseModel):
    name: BandhaPattern
    kannada_name: str
    description: str
    mathematical_rules: str
    typical_length: int
    symmetry_order: int
    historical_source: str
    verification_state: RuleVerificationState = RuleVerificationState.PARTIALLY_VERIFIED
    documentation_level: DocumentationLevel = DocumentationLevel.INFERRED
    provenance_rule_id: str = ""
    is_geometric_visualization_only: bool = False
    authenticity_disclaimer: str = (
        "Coverage statistics reflect geometric completeness across the 27x27 grid. "
        "High coverage does not prove or imply historical authenticity of this traversal sequence."
    )


class BaseBandha(ABC):
    """Abstract base class for all Siri Bhoovalaya Bandha trajectory generators."""

    def __init__(self, metadata: BandhaMetadata):
        self.metadata = metadata

    @abstractmethod
    def generate_steps(
        self,
        start_coord: Tuple[int, int] = (13, 13),
        max_steps: int = 729,
        direction: TraversalDirection = TraversalDirection.FORWARD,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[int, int]]:
        """Generate raw (row, col) coordinate sequence according to mathematical rules."""
        pass

    def validate_bounds(self, coords: List[Tuple[int, int]]) -> Tuple[bool, List[str]]:
        """Verify that every coordinate is strictly within the 27x27 grid [0, 26]."""
        errors = []
        for idx, (r, c) in enumerate(coords):
            if not (0 <= r <= 26 and 0 <= c <= 26):
                errors.append(f"Step {idx} coordinate ({r}, {c}) is outside bounds [0, 26]")
        return len(errors) == 0, errors

    def detect_duplicates(self, coords: List[Tuple[int, int]]) -> List[Dict[str, Any]]:
        """Detect and locate any repeated coordinates in the trajectory."""
        seen: Dict[Tuple[int, int], List[int]] = {}
        for idx, pt in enumerate(coords):
            seen.setdefault(pt, []).append(idx)

        duplicates = []
        for pt, indices in seen.items():
            if len(indices) > 1:
                duplicates.append({
                    "coordinate": [pt[0], pt[1]],
                    "occurrences": len(indices),
                    "step_indices": indices,
                })
        return duplicates

    def calculate_coverage(self, coords: List[Tuple[int, int]]) -> Dict[str, Any]:
        """Compute grid coverage statistics."""
        unique_coords = set(coords)
        return {
            "total_steps": len(coords),
            "unique_cells": len(unique_coords),
            "total_grid_cells": 729,
            "coverage_percentage": round((len(unique_coords) / 729.0) * 100, 2),
        }

    def generate_trajectory(
        self,
        start_coord: Tuple[int, int] = (13, 13),
        max_steps: int = 729,
        direction: TraversalDirection = TraversalDirection.FORWARD,
        params: Optional[Dict[str, Any]] = None,
    ) -> TraversalTrajectory:
        """Generate, validate, and package the complete TraversalTrajectory."""
        raw_coords = self.generate_steps(
            start_coord=start_coord,
            max_steps=max_steps,
            direction=direction,
            params=params,
        )

        is_valid, bound_errors = self.validate_bounds(raw_coords)
        if not is_valid:
            raise ValueError(f"Bandha '{self.metadata.name}' produced out-of-bounds coordinates: {bound_errors[:3]}")

        # Truncate to max_steps if specified
        if max_steps and len(raw_coords) > max_steps:
            raw_coords = raw_coords[:max_steps]

        if direction == TraversalDirection.REVERSE:
            raw_coords = list(reversed(raw_coords))

        steps = [
            CoordinateStep(step_number=idx + 1, row=r, col=c)
            for idx, (r, c) in enumerate(raw_coords)
        ]

        coverage = self.calculate_coverage(raw_coords)
        duplicates = self.detect_duplicates(raw_coords)

        return TraversalTrajectory(
            bandha_name=self.metadata.name,
            steps=steps,
            total_steps=len(steps),
            cycle_length=len(raw_coords) if len(raw_coords) < 729 else None,
            properties={
                "kannada_name": self.metadata.kannada_name,
                "direction": direction.value,
                "coverage_pct": str(coverage["coverage_percentage"]),
                "unique_cells": str(coverage["unique_cells"]),
                "duplicate_count": str(len(duplicates)),
                "mathematical_rules": self.metadata.mathematical_rules,
                "historical_source": self.metadata.historical_source,
            },
        )

    def to_visualization_payload(self, trajectory: TraversalTrajectory) -> Dict[str, Any]:
        """Produce visualization-ready coordinates with relative percentages and vector paths."""
        path_points = []
        for s in trajectory.steps:
            path_points.append({
                "step": s.step_number,
                "row": s.row,
                "col": s.col,
                "x_percent": round(((s.col + 0.5) / 27.0) * 100, 3),
                "y_percent": round(((s.row + 0.5) / 27.0) * 100, 3),
            })

        return {
            "bandha": trajectory.bandha_name.value,
            "total_steps": trajectory.total_steps,
            "points": path_points,
            "metadata": trajectory.properties,
        }

