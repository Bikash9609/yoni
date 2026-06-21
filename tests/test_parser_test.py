"""Deep AST tests for test blocks."""

from pathlib import Path

from yoni import parse_file
from yoni.ast.expr import ExprValue, ProcessOp
from yoni.ast.test import TestAST

FIXTURES = Path(__file__).parent / "fixtures"


def test_when_inputs_and_given_set() -> None:
    result = parse_file(FIXTURES / "test_create_invoice.yoni")
    assert result.ok, result.errors
    assert isinstance(result.ast, TestAST)
    assert len(result.ast.given) == 3
    set_active = result.ast.given[2]
    assert isinstance(set_active, ProcessOp)
    assert set_active.op == "set"
    assert isinstance(set_active.value, ExprValue)
    assert set_active.value.value is True
    email_set = result.ast.given[1]
    assert email_set.value == "test@example.com"
    assert result.ast.when is not None
    assert len(result.ast.when.inputs) == 2
    assert result.ast.when.inputs[0].name == "order_id"
    assert result.ast.when.inputs[0].value == "ORD_001"


def test_expect_eq_right_side() -> None:
    result = parse_file(FIXTURES / "test_create_invoice.yoni")
    eq_ops = [e for e in result.ast.expect if e.op == "eq"]
    assert len(eq_ops) == 2
    assert eq_ops[0].right.name == "customer.customer_id"
    assert eq_ops[1].right.name == "STS_INVOICE_001.Draft"
