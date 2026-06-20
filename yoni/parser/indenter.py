"""Lark indenter for Yoni's indentation-based syntax.

Yoni uses 2-space indentation under section headers (docs/01-yoni-language-spec.md).
"""

from lark.indenter import Indenter


class YoniIndenter(Indenter):
    """Convert _NEWLINE tokens into _INDENT / _DEDENT for nested sections."""

    NL_type = "_NEWLINE"
    OPEN_PAREN_types: list[str] = []
    CLOSE_PAREN_types: list[str] = []
    INDENT_type = "_INDENT"
    DEDENT_type = "_DEDENT"
    tab_len = 2
