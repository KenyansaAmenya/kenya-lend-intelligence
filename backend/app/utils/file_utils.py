# File Utility Functions.
# To handle file validation, parsing, and security checks.

import hashlib
import magic
from pathlib import Path
from typing import Optional, Tuple

from fastapi import UploadFile

from app.core.logging_config import get_logger

logger = get_logger(__name__)


ALLOWED_EXTENSIONS = {
    "csv", "xlsx", "xls", "pdf",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_file(file: UploadFile) -> Tuple[bool, Optional[str]]:

    # Check file size
    if file.size and file.size > MAX_FILE_SIZE:
        return False, f"File size exceeds maximum of {MAX_FILE_SIZE / 1024 / 1024}MB"
    
    # Check extension
    ext = Path(file.filename or "").suffix.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type: {ext}"
    
    # Check MIME type
    allowed_mimes = [
        "text/csv",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/pdf",
    ]
    
    if file.content_type not in allowed_mimes:
        return False, f"Unsupported MIME type: {file.content_type}"
    
    return True, None

def calculate_file_hash(content: bytes) -> str:
    # Calculate SHA-256 hash of file content.
    return hashlib.sha256(content).hexdigest()

def sanitize_filename(filename: str) -> str:
    # Sanitize filename for safe storage.
    from re import sub
    
    # Remove path components
    name = Path(filename).name
    
    # Remove unsafe characters
    safe = sub(r'[^a-zA-Z0-9._-]', '_', name)
    
    return safe


# TODO: Add virus scanning integration
# TODO: Add file encryption for sensitive data
# TODO: Add secure deletion for temporary files