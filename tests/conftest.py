"""Pytest fixtures and configuration."""
import os
import shutil
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from clio.api.app import create_app
from clio.config import settings
from clio.storage.db import Base, get_db
from tests.synthetic_data import generate_synthetic_pdf_bytes


@pytest.fixture(scope="session")
def synthetic_pdf() -> bytes:
    """Provides deterministically generated synthetic PDF fixture."""
    return generate_synthetic_pdf_bytes()


@pytest.fixture
def test_db():
    """Provides an isolated database session for each test using StaticPool."""
    test_db_url = "sqlite:///:memory:"
    engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """Provides a TestClient with database dependency overridden."""
    app = create_app()

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
