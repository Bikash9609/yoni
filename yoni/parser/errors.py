"""Re-export parse errors for backward compatibility within parser package."""

from yoni.errors import (
    ParseError,
    missing_required_field,
    section_order_violation,
    syntax_error,
    unimplemented_block,
)

__all__ = [
    "ParseError",
    "missing_required_field",
    "section_order_violation",
    "syntax_error",
    "unimplemented_block",
]
