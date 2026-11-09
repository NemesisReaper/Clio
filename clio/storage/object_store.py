"""Object storage abstraction for documents, rendered page images, and cell crops."""
import hashlib
import os
import shutil
from pathlib import Path
from typing import Optional, Tuple
from clio.config import settings


class ObjectStore:
    """Manages file storage on disk with deterministic, content-addressed paths."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or settings.data_dir
        self.pdf_dir = self.base_dir / "pdfs"
        self.pages_dir = self.base_dir / "pages"
        self.crops_dir = self.base_dir / "crops"
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.pages_dir.mkdir(parents=True, exist_ok=True)
        self.crops_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def calculate_sha256(data: bytes) -> str:
        """Compute hex digest SHA-256 for binary content."""
        return hashlib.sha256(data).hexdigest()

    def save_pdf(self, content: bytes, filename: str) -> Tuple[str, str]:
        """Save raw PDF content.

        Returns:
            (document_id, file_path_str)
        """
        sha256 = self.calculate_sha256(content)
        doc_id = f"doc_{sha256[:16]}"
        target_path = self.pdf_dir / f"{doc_id}_{filename}"
        with open(target_path, "wb") as f:
            f.write(content)
        return doc_id, str(target_path)

    def save_page_image(self, image_bytes: bytes, doc_id: str, page_number: int) -> str:
        """Save a rendered page image as PNG.

        Returns:
            file_path_str
        """
        page_filename = f"{doc_id}_page_{page_number:04d}.png"
        target_path = self.pages_dir / page_filename
        with open(target_path, "wb") as f:
            f.write(image_bytes)
        return str(target_path)

    def save_cell_crop(
        self, crop_bytes: bytes, chakra_id: str, row: int, col: int
    ) -> str:
        """Save a cropped 27x27 cell image for manual audit.

        Returns:
            file_path_str
        """
        cell_filename = f"{chakra_id}_r{row:02d}_c{col:02d}.png"
        target_path = self.crops_dir / cell_filename
        with open(target_path, "wb") as f:
            f.write(crop_bytes)
        return str(target_path)

    def get_file_bytes(self, file_path: str) -> Optional[bytes]:
        """Read bytes from storage."""
        p = Path(file_path)
        if p.exists() and p.is_file():
            with open(p, "rb") as f:
                return f.read()
        return None


# Global singleton instance
object_store = ObjectStore()

