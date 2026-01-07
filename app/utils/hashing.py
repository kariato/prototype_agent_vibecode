"""
app/utils/hashing.py

Utilities for calculating SHA-256 hashes of files and strings.
Used for integrity verification in PatchOps and DocOps.
"""

import hashlib
from pathlib import Path
from typing import Optional

def calculate_file_hash(file_path: Path) -> Optional[str]:
    """Calculates SHA-256 hash of a file."""
    if not file_path.exists():
        return None
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def calculate_content_hash(content: str) -> str:
    """Calculates SHA-256 hash of a string content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
