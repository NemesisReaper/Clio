"""Health check endpoint."""
from fastapi import APIRouter
from clio.config import settings
from clio.storage.graph_store import graph_store

router = APIRouter(tags=["Health"])


@router.get("/health")
def get_health():
    """Service health status and connected storage engines."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.environment,
        "storage": {
            "neo4j_connected": graph_store.driver is not None,
            "property_graph_nodes": len(graph_store.nodes_registry),
            "property_graph_edges": len(graph_store.edges_registry),
        },
    }

