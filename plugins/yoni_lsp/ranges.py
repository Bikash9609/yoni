"""Map ParseError diagnostics to LSP ranges."""

from __future__ import annotations

import re

from lsprotocol import types

from yoni.errors import ParseError

_SECTION_ORDER_FOUND = re.compile(r"found '(\w+)'", re.IGNORECASE)


def error_to_range(source: str, error: ParseError) -> types.Range:
    """Return an LSP range for a parse diagnostic."""
    lines = source.splitlines()
    if not lines:
        return types.Range(
            start=types.Position(line=0, character=0),
            end=types.Position(line=0, character=0),
        )

    start_line, start_col, end_line, end_col = _resolve_bounds(source, error, lines)
    return types.Range(
        start=types.Position(line=start_line, character=start_col),
        end=types.Position(line=end_line, character=end_col),
    )


def _resolve_bounds(
    source: str, error: ParseError, lines: list[str]
) -> tuple[int, int, int, int]:
    if error.line is not None:
        line_idx = max(error.line - 1, 0)
        if line_idx < len(lines):
            line_text = lines[line_idx]
            start_col = max((error.column or 1) - 1, 0)
            start_col = min(start_col, max(len(line_text), 1))
            return line_idx, start_col, line_idx, max(len(line_text), start_col + 1)

    if error.code == "YONI1007":
        match = _SECTION_ORDER_FOUND.search(error.message)
        if match:
            section = match.group(1)
            for index, line in enumerate(lines):
                if re.match(rf"^\s*{re.escape(section)}:\s*$", line, re.IGNORECASE):
                    return index, 0, index, max(len(line), 1)

    if error.code == "YONI1003":
        return 0, 0, 0, max(len(lines[0]), 1)

    if error.block_id:
        for index, line in enumerate(lines):
            compact = line.replace(" ", "")
            if f"id:{error.block_id}" in compact:
                return index, 0, index, max(len(line), 1)

    return 0, 0, 0, max(len(lines[0]), 1)
