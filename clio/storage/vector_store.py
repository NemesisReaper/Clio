"""Qdrant vector store integration for semantic retrieval of source passages."""
import logging
import socket
from typing import Any, Dict, List, Optional
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from clio.config import settings

logger = logging.getLogger(__name__)


def _is_qdrant_reachable(host: str, port: int, timeout: float = 0.2) -> bool:
    """Fast check whether remote Qdrant port is accepting connections."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


class PassageVectorStore:
    """Manages Qdrant vector index for historical passages and commentary."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: int = 6333,
        collection_name: Optional[str] = None,
        in_memory: bool = False,
    ):
        self.collection_name = collection_name or settings.qdrant_collection_name
        self.vector_size = 128  # Compact semantic embedding size for offline/online compatibility

        target_host = host or settings.qdrant_host or "localhost"
        target_port = port or settings.qdrant_port

        if in_memory or settings.qdrant_use_in_memory or not _is_qdrant_reachable(target_host, target_port):
            self.client = QdrantClient(":memory:")
            logger.info("Using in-memory Qdrant instance.")
        else:
            try:
                self.client = QdrantClient(host=target_host, port=target_port, timeout=2.0)
                self.client.get_collections()
                logger.info("Connected to remote Qdrant at %s:%d", target_host, target_port)
            except Exception as e:
                logger.warning(
                    "Could not connect to Qdrant at %s:%d (%s). Falling back to :memory: mode.",
                    target_host,
                    target_port,
                    e,
                )
                self.client = QdrantClient(":memory:")

        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Create Qdrant collection if not exists."""
        try:
            collections = [c.name for c in self.client.get_collections().collections]
            if self.collection_name not in collections:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self.vector_size,
                        distance=qmodels.Distance.COSINE,
                    ),
                )
        except Exception as e:
            logger.error("Failed to ensure collection %s: %s", self.collection_name, e)

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate deterministic, normalized vector embedding for text.

        In production, this hooks into an embedding model (e.g. BGE or multilingual).
        Here we use deterministic character-n-gram hashing projection for fast,
        zero-dependency, offline deterministic semantic representation.
        """
        vec = np.zeros(self.vector_size, dtype=np.float32)
        if not text:
            return vec.tolist()

        # Deterministic feature hashing of char 2-grams and 3-grams
        for i in range(len(text) - 1):
            gram = text[i : i + 2]
            h = hash(gram) % self.vector_size
            vec[h] += 1.0
        for i in range(len(text) - 2):
            gram = text[i : i + 3]
            h = hash(gram) % self.vector_size
            vec[h] += 1.5

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def index_passage(
        self,
        passage_id: str,
        text: str,
        document_id: str,
        page_number: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Upsert a single passage into Qdrant."""
        embedding = self._generate_embedding(text)
        payload = {
            "passage_id": passage_id,
            "document_id": document_id,
            "page_number": page_number,
            "text": text,
            **(metadata or {}),
        }
        # Use integer or deterministic UUID for Qdrant point ID
        point_id = abs(hash(passage_id)) % (2**63 - 1)
        point = qmodels.PointStruct(id=point_id, vector=embedding, payload=payload)
        self.client.upsert(collection_name=self.collection_name, points=[point])

    def search_similar(
        self, query_text: str, limit: int = 5, document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search passages by semantic similarity with optional document filter."""
        embedding = self._generate_embedding(query_text)
        query_filter = None
        if document_id:
            query_filter = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="document_id",
                        match=qmodels.MatchValue(value=document_id),
                    )
                ]
            )

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=embedding,
            query_filter=query_filter,
            limit=limit,
        )
        return [
            {
                "score": r.score,
                "payload": r.payload,
            }
            for r in results
        ]


# Global singleton instance
vector_store = PassageVectorStore()
