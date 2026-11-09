"""FastAPI Application factory for Siri Bhoovalaya Platform."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from clio.api.routes import decipherment, documents, graph, health
from clio.config import settings
from clio.storage.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle startup and shutdown handler."""
    # Ensure directories & database tables exist
    settings.ensure_directories()
    init_db()
    yield
    # Shutdown cleanups if any


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description=(
            "Siri Bhoovalaya Agentic Decipherment Platform — Stage A Foundation: "
            "Document Digitization, 27x27 Chakra Matrix Extraction, Halegannada Shloka "
            "Preservation, and Middle-Out Historical Knowledge Graph."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(health.router)
    app.include_router(documents.router)
    app.include_router(graph.router)
    app.include_router(decipherment.router)

    return app


app = create_app()

