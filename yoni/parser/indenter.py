"""Lark indenter for Yoni's indentation-based syntax.

Yoni uses 2-space indentation under section headers (docs/01-yoni-language-spec.md).
Tabs are rejected (YONI1008).
"""

from __future__ import annotations

from lark.indenter import Indenter


class YoniIndenter(Indenter):
    """Convert _NEWLINE tokens into _INDENT / _DEDENT for nested sections."""

    NL_type = "_NEWLINE"
    OPEN_PAREN_types: list[str] = []
    CLOSE_PAREN_types: list[str] = []
    INDENT_type = "_INDENT"
    DEDENT_type = "_DEDENT"
    tab_len = 2

    def __init__(self) -> None:
        super().__init__()
        self.tab_errors: list[tuple[int, str]] = []

    def handle_NL(self, token):  # type: ignore[no-untyped-def]
        text = str(token)
        if "\t" in text:
            line_no = getattr(token, "line", None) or 0
            self.tab_errors.append((line_no, text))
        return super().handle_NL(token)
