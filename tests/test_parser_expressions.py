"""Expression parsing edge cases."""

from yoni import parse_source
from yoni.ast.expr import ExprCall, ExprRef, ExprValue, ExprVar
from yoni.ast.rule import RuleAST


def test_expr_refs_and_ops() -> None:
    source = """rule Refs

id: RULE_REFS_001
desc:
  Ref and enum expr.

expression:
  @Entity.Customer == Draft
"""
    result = parse_source(source)
    assert result.ok, result.errors


def test_expr_call() -> None:
    source = """rule Call

id: RULE_CALL_001
desc:
  Call expression.

expression:
  count(a, b) > 0
"""
    result = parse_source(source)
    assert result.ok, result.errors
    expr = result.ast.expression
    assert expr.op == ">"
