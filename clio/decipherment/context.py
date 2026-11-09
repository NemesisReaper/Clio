"""Historical context retrieval from Knowledge Graph for deciphered passages."""
import logging
from typing import List, Optional

from clio.models.graph import TraversalRequest, TraversalResult
from clio.storage.graph_store import graph_store

logger = logging.getLogger(__name__)


class HistoricalContextRetriever:
    """Retrieves context and entity subgraphs relevant to deciphered verses."""

    # Keywords to Canonical Entities mapping
    ENTITY_KEYWORD_MAP = {
        "ಸ್ಯಾದ್ವಾದ": "concept_bandha",
        "ಜಿನ": "person_kumudendu_muni",
        "ಕುಮುದೇಂದು": "person_kumudendu_muni",
        "ಸಿರಿಭೂವಲಯ": "work_siri_bhoovalaya",
        "ಷಟ್ಖಂಡಾಗಮ": "work_shatkhandagama",
        "ಧಾರಸೇನ": "person_dharasena",
        "ಸರ್ವತೋಭದ್ರ": "concept_sarvatobhadra",
        "ಅಂಕಫಲ": "concept_ankaphala",
        "ಹಳೆಗನ್ನಡ": "lang_halegannada",
    }

    async def retrieve_context(
        self,
        verse_text: str,
        anchor_id: Optional[str] = None,
        max_depth: int = 2,
    ) -> Optional[TraversalResult]:
        """Identify entities mentioned in verse and query knowledge graph around them."""
        target_anchor = anchor_id

        if not target_anchor:
            for kw, eid in self.ENTITY_KEYWORD_MAP.items():
                if kw in verse_text:
                    target_anchor = eid
                    break

        if not target_anchor:
            target_anchor = "work_siri_bhoovalaya"

        try:
            req = TraversalRequest(
                anchor_id=target_anchor,
                max_depth=max_depth,
                direction="BOTH",
                include_hypotheses=True,
            )
            result = graph_store.traverse_middle_out(req)
            return result
        except Exception as e:
            logger.warning("Could not retrieve graph context for '%s': %s", target_anchor, e)
            return None


context_retriever = HistoricalContextRetriever()
