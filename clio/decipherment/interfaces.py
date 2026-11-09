"""Stage B typed protocols and abstract interfaces.

These interfaces define the architecture for the upcoming Stage B decipherment
pipeline, ensuring clean separation of concerns without prematurely claiming
unimplemented decipherment capabilities on Day 1.
"""
from typing import Dict, List, Optional, Protocol, Tuple, runtime_checkable

from clio.models.chakra import ChakraMatrix
from clio.models.decipherment import (
    AlignedVerseCandidate,
    BandhaPattern,
    CoordinateStep,
    DeciphermentExplanation,
    DeciphermentRequest,
    DeciphermentResult,
    PhoneticMapping,
    TraversalTrajectory,
)
from clio.models.graph import TraversalResult


@runtime_checkable
class IChakraRetriever(Protocol):
    """Retrieves validated 27x27 Chakra matrices by ID or document reference."""

    async def get_chakra(self, chakra_id: str) -> Optional[ChakraMatrix]:
        """Fetch a Chakra matrix by unique identifier."""
        ...

    async def list_chakras_for_document(self, document_id: str) -> List[ChakraMatrix]:
        """Fetch all Chakra matrices associated with a document."""
        ...


@runtime_checkable
class IBandhaSelector(Protocol):
    """Selects and configures geometric traversal bandhas."""

    def get_supported_bandhas(self) -> List[BandhaPattern]:
        """Return list of supported Bandha patterns."""
        ...

    def validate_bandha_compatibility(
        self, matrix: ChakraMatrix, bandha: BandhaPattern
    ) -> bool:
        """Verify whether a matrix satisfies geometric preconditions for a bandha."""
        ...


@runtime_checkable
class INumericalTraverser(Protocol):
    """Executes geometric traversal algorithms across 27x27 grid coordinates."""

    def generate_trajectory(
        self,
        bandha: BandhaPattern,
        start_coord: Tuple[int, int] = (13, 13),
        max_steps: int = 729,
        params: Optional[Dict[str, str]] = None,
    ) -> TraversalTrajectory:
        """Compute the sequence of coordinates for a given bandha."""
        ...

    def extract_numerical_stream(
        self, matrix: ChakraMatrix, trajectory: TraversalTrajectory
    ) -> List[int]:
        """Read values from the Chakra along the trajectory."""
        ...


@runtime_checkable
class IPhoneticSubstitutor(Protocol):
    """Substitutes numerical values (1-64) with Halegannada aksharas/phonemes."""

    def get_ankaphala_table(self) -> Dict[int, PhoneticMapping]:
        """Retrieve the documented Siri Bhoovalaya numerical-to-akshara map."""
        ...

    def substitute(self, numbers: List[int]) -> str:
        """Convert a sequence of numbers into an Halegannada character stream."""
        ...


@runtime_checkable
class IShlokaAligner(Protocol):
    """Aligns raw akshara stream into metered verse segments (Chhandas)."""

    def segment_words(self, raw_stream: str) -> str:
        """Apply Halegannada morphological and sandhi rules to segment words."""
        ...

    def align_to_meter(self, segmented_stream: str) -> AlignedVerseCandidate:
        """Match candidate segments against classical Halegannada poetic meters."""
        ...


@runtime_checkable
class IHistoricalContextRetriever(Protocol):
    """Queries the historical knowledge graph for entities and context referenced in verse."""

    async def retrieve_context(
        self, entities: List[str], max_depth: int = 2
    ) -> TraversalResult:
        """Retrieve historical subgraph centered around identified entities."""
        ...


@runtime_checkable
class IEnglishExplainer(Protocol):
    """Generates rigorous historical and semantic English explanations."""

    async def explain(
        self, verse: AlignedVerseCandidate, context: TraversalResult
    ) -> Tuple[str, str]:
        """Returns (english_translation, english_historical_commentary)."""
        ...


@runtime_checkable
class IModernKannadaExplainer(Protocol):
    """Generates authentic Modern Kannada explanations (ಹೊಸಗನ್ನಡ ವಿವರಣೆ)."""

    async def explain(
        self, verse: AlignedVerseCandidate, context: TraversalResult
    ) -> Tuple[str, str]:
        """Returns (modern_kannada_translation, modern_kannada_commentary)."""
        ...


@runtime_checkable
class IDeciphermentOrchestrator(Protocol):
    """Coordinates the end-to-end Stage B decipherment pipeline."""

    async def decipher(self, request: DeciphermentRequest) -> DeciphermentResult:
        """Execute full decipherment pipeline."""
        ...

