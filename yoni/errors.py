"""Parse-time diagnostics for the Yoni compiler.

Diagnostics target stable block IDs, not line numbers (docs/01-yoni-language-spec.md).
Parse errors use the YONI1000 range.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ParseError(BaseModel):
    """A single parse diagnostic."""

    code: str
    severity: Literal["error", "warning"] = "error"
    message: str
    file: str = ""
    block_id: str | None = None
    suggestion: str | None = None
    line: int | None = None


def syntax_error(
    message: str,
    *,
    file: str = "",
    line: int | None = None,
    block_id: str | None = None,
) -> ParseError:
    """YONI1001 — Lark could not parse the source."""
    return ParseError(
        code="YONI1001",
        message=message,
        file=file,
        line=line,
        block_id=block_id,
    )


def unimplemented_block(
    kind: str,
    *,
    file: str = "",
    block_id: str | None = None,
) -> ParseError:
    """YONI1002 — Block kind recognized but transformer not yet implemented."""
    return ParseError(
        code="YONI1002",
        message=f"Block kind '{kind}' is recognized but not yet implemented.",
        file=file,
        block_id=block_id,
        suggestion="Implement transformer for this block kind.",
    )


def missing_required_field(
    field: str,
    *,
    file: str = "",
    block_id: str | None = None,
) -> ParseError:
    """YONI1003 — Mandatory id: or desc: missing."""
    return ParseError(
        code="YONI1003",
        message=f"Missing required field: {field}",
        file=file,
        block_id=block_id,
        suggestion=f"Add '{field}:' to the block.",
    )


def section_order_violation(
    expected: str,
    found: str,
    *,
    file: str = "",
    block_id: str | None = None,
) -> ParseError:
    """YONI1007 — Intent sections out of order."""
    return ParseError(
        code="YONI1007",
        message=f"Intent sections are out of order: expected '{expected}', found '{found}'.",
        file=file,
        block_id=block_id,
        suggestion=f"Move '{found}:' below '{expected}:'.",
    )
