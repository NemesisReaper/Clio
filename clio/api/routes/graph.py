"""FastAPI routes for Middle-Out Graph Traversal."""
from fastapi import APIRouter, HTTPException, status
from clio.models.graph import TraversalRequest, TraversalResult
from clio.storage.graph_store import graph_store

router = APIRouter(prefix="/api/v1/graph", tags=["Knowledge Graph"])


@router.post("/traverse", response_model=TraversalResult)
def traverse_graph(request: TraversalRequest):
    """Execute middle-out graph traversal expanding from an anchor entity."""
    try:
        result = graph_store.traverse_middle_out(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Traversal execution failed: {e}",
        )

