"""Post-generation verification for deterministic artifacts."""

from __future__ import annotations

import re

_MARKER_RE = re.compile(r"^#\s*yoni:([A-Z0-9_]+)\s*$", re.MULTILINE)


def extract_block_markers(content: str) -> set[str]:
    return set(_MARKER_RE.findall(content))


def verify_content(content: str, required_block_ids: list[str]) -> list[str]:
    """Return verification error messages (empty if ok)."""
    errors: list[str] = []
    found = extract_block_markers(content)
    for block_id in required_block_ids:
        if block_id not in found:
            errors.append(f"Missing required marker # yoni:{block_id}")
    if not found:
        errors.append("No # yoni:BLOCK_ID markers found in generated content")
    return errors
