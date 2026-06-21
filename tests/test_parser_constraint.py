"""Deep AST tests for constraint blocks."""

from pathlib import Path

from yoni import parse_file
from yoni.ast.constraint import ConstraintAST
from yoni.ast.expr import ExprBinary, ExprCall

FIXTURES = Path(__file__).parent / "fixtures"


def test_constraint_check_call_expr() -> None:
    result = parse_file(FIXTURES / "constraint_email_unique.yoni")
    assert result.ok, result.errors
    assert isinstance(result.ast, ConstraintAST)
    check = result.ast.check
    assert isinstance(check, ExprBinary)
    assert check.op == "=="
    assert isinstance(check.left, ExprCall)
    assert check.left.op == "count"
