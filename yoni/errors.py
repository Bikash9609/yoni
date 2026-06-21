"""Parse-time diagnostics for the Yoni compiler."""

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
    column: int | None = None


def syntax_error(
    message: str,
    *,
    file: str = "",
    line: int | None = None,
    column: int | None = None,
    block_id: str | None = None,
) -> ParseError:
    """YONI1001 — Lark could not parse the source."""
    return ParseError(
        code="YONI1001",
        message=message,
        file=file,
        line=line,
        column=column,
        block_id=block_id,
    )


def unexpected_token(
    token: str,
    *,
    expected: str | None = None,
    file: str = "",
    line: int | None = None,
    column: int | None = None,
    block_id: str | None = None,
) -> ParseError:
    """YONI1002 — Unexpected token at a specific source location."""
    location = ""
    if line is not None:
        location = f" at line {line}"
        if column is not None:
            location += f", column {column}"
    hint = f" Expected: {expected}." if expected else ""
    return ParseError(
        code="YONI1002",
        message=f"Unexpected token {token!r}{location}.{hint}",
        file=file,
        line=line,
        column=column,
        block_id=block_id,
        suggestion="Check indentation, section headers, and typed @Type.Name references.",
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


def unknown_section(
    section: str,
    kind: str,
    *,
    file: str = "",
    block_id: str | None = None,
) -> ParseError:
    """YONI1005 — Section not allowed for this block kind."""
    return ParseError(
        code="YONI1005",
        message=f"Section '{section}' is not allowed in {kind} blocks.",
        file=file,
        block_id=block_id,
    )


def missing_mandatory_section(
    section: str,
    *,
    file: str = "",
    block_id: str | None = None,
) -> ParseError:
    """YONI1006 — Required section missing."""
    return ParseError(
        code="YONI1006",
        message=f"Missing mandatory section: {section}",
        file=file,
        block_id=block_id,
        suggestion=f"Add '{section}:' section to the block.",
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


def tab_in_indent(
    *,
    file: str = "",
    line: int | None = None,
    block_id: str | None = None,
) -> ParseError:
    """YONI1008 — Tab character used for indentation."""
    return ParseError(
        code="YONI1008",
        message="Tabs are not allowed for indentation; use 2 spaces.",
        file=file,
        line=line,
        block_id=block_id,
    )


def duplicate_section(
    section: str,
    *,
    file: str = "",
    block_id: str | None = None,
) -> ParseError:
    """YONI1009 — Duplicate section header."""
    return ParseError(
        code="YONI1009",
        message=f"Duplicate section: {section}",
        file=file,
        block_id=block_id,
    )


def unknown_block_kind(
    kind: str,
    *,
    file: str = "",
    block_id: str | None = None,
) -> ParseError:
    """YONI1004 — Unknown block kind after parse."""
    return ParseError(
        code="YONI1004",
        message=f"Unknown block kind: {kind}",
        file=file,
        block_id=block_id,
    )
