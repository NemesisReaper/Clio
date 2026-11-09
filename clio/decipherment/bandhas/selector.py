"""Bandha selector and numerical matrix trajectory executor."""
import logging
from typing import Dict, List, Optional, Tuple, Type

from clio.models.chakra import ChakraMatrix
from clio.models.decipherment import (
    BandhaPattern,
    TraversalTrajectory,
)
from clio.decipherment.bandhas.base import BaseBandha, TraversalDirection
from clio.decipherment.bandhas.sarvatobhadra import SarvatobhadraBandha
from clio.decipherment.bandhas.padmabandha import Padmabandha
from clio.decipherment.bandhas.gomutrika import GomutrikaBandha
from clio.decipherment.bandhas.chakrabandha import Chakrabandha

logger = logging.getLogger(__name__)


class BandhaEngine:
    """Manages Bandha registry, validation, trajectory computation, and numerical extraction."""

    def __init__(self):
        self._registry: Dict[BandhaPattern, BaseBandha] = {}
        self._register_default_bandhas()

    def _register_default_bandhas(self) -> None:
        self.register_bandha(SarvatobhadraBandha())
        self.register_bandha(Padmabandha())
        self.register_bandha(GomutrikaBandha())
        self.register_bandha(Chakrabandha())

    def register_bandha(self, bandha_instance: BaseBandha) -> None:
        self._registry[bandha_instance.metadata.name] = bandha_instance

    def get_supported_bandhas(self) -> List[BandhaPattern]:
        """Return list of supported Bandha patterns."""
        return list(self._registry.keys())

    def get_bandha(self, bandha_name: BandhaPattern) -> BaseBandha:
        """Fetch Bandha generator instance."""
        if bandha_name not in self._registry:
            raise ValueError(f"Bandha '{bandha_name}' is not supported or implemented.")
        return self._registry[bandha_name]

    def validate_bandha_compatibility(
        self, matrix: ChakraMatrix, bandha: BandhaPattern
    ) -> bool:
        """Verify whether matrix satisfies geometric preconditions."""
        if matrix.rows != 27 or matrix.cols != 27:
            return False
        if matrix.expected_cells != 729:
            return False
        # If matrix is empty or invalid
        if not matrix.matrix_grid or len(matrix.matrix_grid) != 27:
            return False
        return True

    def generate_trajectory(
        self,
        bandha: BandhaPattern,
        start_coord: Tuple[int, int] = (13, 13),
        max_steps: int = 729,
        params: Optional[Dict[str, str]] = None,
    ) -> TraversalTrajectory:
        """Compute the sequence of coordinates for a given bandha."""
        bandha_impl = self.get_bandha(bandha)
        direction = TraversalDirection.FORWARD
        if params and "direction" in params:
            try:
                direction = TraversalDirection(params["direction"].upper())
            except ValueError:
                direction = TraversalDirection.FORWARD

        return bandha_impl.generate_trajectory(
            start_coord=start_coord,
            max_steps=max_steps,
            direction=direction,
            params=params,
        )

    def extract_numerical_stream(
        self, matrix: ChakraMatrix, trajectory: TraversalTrajectory
    ) -> List[int]:
        """Read integer values from the Chakra matrix along the trajectory.

        Crucial rule: Do not silently fill missing or unreadable cells!
        """
        numerical_stream: List[int] = []
        grid = matrix.matrix_grid

        for step in trajectory.steps:
            r, c = step.row, step.col
            val = grid[r][c]
            if val is None:
                raise ValueError(
                    f"Matrix cell at row {r}, col {c} (step {step.step_number}) is unreadable or None. "
                    "Cannot silently fill missing cells for decipherment."
                )
            numerical_stream.append(val)
            step.cell_value = val

        return numerical_stream


bandha_engine = BandhaEngine()
