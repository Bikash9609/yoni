"""Deep AST tests for rule blocks."""

from pathlib import Path

from yoni import parse_file, parse_source
from yoni.ast.expr import ExprBinary, ExprValue, ExprVar
from yoni.ast.rule import RuleAST

FIXTURES = Path(__file__).parent / "fixtures"


def test_rule_expression_ge() -> None:
    result = parse_file(FIXTURES / "rule_adult.yoni")
    assert result.ok, result.errors
    assert isinstance(result.ast, RuleAST)
    expr = result.ast.expression
    assert isinstance(expr, ExprBinary)
    assert expr.op == ">="
    assert isinstance(expr.left, ExprVar)
    assert expr.left.name == "age"
    assert isinstance(expr.right, ExprValue)
    assert expr.right.value == 18


def test_rule_bool_literal() -> None:
    source = """rule Active

id: RULE_ACTIVE_001
desc:
  Checks active flag.

expression:
  active == true
"""
    result = parse_source(source)
    assert result.ok, result.errors
    expr = result.ast.expression
    assert isinstance(expr, ExprBinary)
    assert isinstance(expr.right, ExprValue)
    assert expr.right.type == "boolean"
    assert expr.right.value is True


def test_rule_paren_expression() -> None:
    source = """rule AdultParen

id: RULE_PAREN_001
desc:
  Paren expression.

expression:
  (age + 1) >= 18
"""
    result = parse_source(source)
    assert result.ok, result.errors
    assert isinstance(result.ast.expression, ExprBinary)
