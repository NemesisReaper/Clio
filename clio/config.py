"""Configuration management for Clio Siri Bhoovalaya platform."""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable overrides."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Service identification
    app_name: str = "Siri Bhoovalaya Decipherment Platform"
    environment: str = "development"
    debug: bool = True

    # Storage paths
    data_dir: Path = Path("./data")
    pdf_storage_dir: Path = Path("./data/pdfs")
    pages_storage_dir: Path = Path("./data/pages")
    crops_storage_dir: Path = Path("./data/crops")

    # Database URLs
    # By default in standalone test/dev mode we can use SQLite if Postgres is unavailable,
    # or the configured Postgres URI when running under Docker Compose.
    database_url: str = "sqlite+aiosqlite:///./data/clio.db"
    sync_database_url: str = "sqlite:///./data/clio.db"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "clio"
    postgres_user: str = "clio_user"
    postgres_password: str = "clio_secret"

    # Neo4j Graph DB
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "siri_bhoovalaya_secret"
    neo4j_database: str = "neo4j"

    # Qdrant Vector DB
    qdrant_host: Optional[str] = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "siri_bhoovalaya_passages"
    qdrant_use_in_memory: bool = False

    # Document Ingestion & Image Processing
    render_dpi: int = 300
    scanned_text_density_threshold: float = 0.05
    matrix_grid_dimension: int = 27
    matrix_expected_cell_count: int = 729
    matrix_domain_min: int = 1
    matrix_domain_max: int = 64
    matrix_domain_extended_max: int = 729
    ocr_confidence_threshold: float = 0.70

    def ensure_directories(self) -> None:
        """Ensure all storage directories exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_storage_dir.mkdir(parents=True, exist_ok=True)
        self.pages_storage_dir.mkdir(parents=True, exist_ok=True)
        self.crops_storage_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()

