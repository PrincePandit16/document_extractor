import os
import uuid
import shutil
from pathlib import Path
from typing import Tuple
from loguru import logger
from config.settings import settings
from app.utils.exceptions import FileValidationException
from app.utils.logging import log_execution


MIME_TYPE_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".pdf": "application/pdf",
}


class FileService:
    """Handles file upload, validation, and storage."""

    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        self.allowed_extensions = {f".{ext}" for ext in settings.ALLOWED_EXTENSIONS}

    @log_execution
    def save_upload(self, file_content: bytes, original_filename: str) -> Tuple[str, str, str, int]:
        """
        Validate and save uploaded file.
        Returns (saved_filename, file_path, mime_type, file_size).
        """
        # Validate extension
        ext = Path(original_filename).suffix.lower()
        if ext not in self.allowed_extensions:
            raise FileValidationException(
                f"File type '{ext}' not allowed. Allowed: {self.allowed_extensions}"
            )

        # Validate size
        file_size = len(file_content)
        if file_size > self.max_size:
            raise FileValidationException(
                f"File size {file_size/1024/1024:.1f}MB exceeds limit {settings.MAX_FILE_SIZE_MB}MB"
            )

        # Generate unique filename
        unique_name = f"{uuid.uuid4().hex}{ext}"
        file_path = self.upload_dir / unique_name

        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)

        mime_type = MIME_TYPE_MAP.get(ext, "application/octet-stream")
        logger.info(f"Saved file: {unique_name} ({file_size} bytes)")
        return unique_name, str(file_path), mime_type, file_size

    def delete_file(self, file_path: str) -> bool:
        """Delete a file from disk."""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Deleted file: {file_path}")
            return True
        except Exception as e:
            logger.warning(f"Failed to delete file {file_path}: {e}")
            return False

    def get_file_path(self, filename: str) -> str:
        return str(self.upload_dir / filename)
