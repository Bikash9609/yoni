"""Deep AST tests for view blocks."""

from pathlib import Path

from yoni import parse_file
from yoni.ast.view import ViewAST

FIXTURES = Path(__file__).parent / "fixtures"


def test_view_fields_and_layout() -> None:
    result = parse_file(FIXTURES / "view_customer_list.yoni")
    assert result.ok, result.errors
    assert isinstance(result.ast, ViewAST)
    assert result.ast.fields == ["customer_id", "email", "active"]
    assert result.ast.query is not None
    assert len(result.ast.actions) == 1
    assert result.ast.layout is not None
    assert result.ast.layout.entries["type"] == "table"
    assert result.ast.layout.entries["columns"] == 3
