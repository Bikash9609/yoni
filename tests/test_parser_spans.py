"""SourceSpan wiring tests."""

from yoni import parse_source


def test_block_span_populated() -> None:
    source = """entity Customer

id: ENT_SPAN_001
desc:
  Span test.

fields:
  id: s
"""
    result = parse_source(source)
    assert result.ok, result.errors
    assert result.ast.span is not None
    assert result.ast.span.start_line >= 1
    assert result.ast.span.file == "<stdin>"
