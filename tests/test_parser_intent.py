"""Smoke tests for intent block parsing."""

from pathlib import Path

from yoni import parse_file
from yoni.ast.intent import IntentAST

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_intent_create_invoice() -> None:
    result = parse_file(FIXTURES / "intent_create_invoice.yoni")
    assert result.ok, result.errors
    assert isinstance(result.ast, IntentAST)
    assert result.ast.id == "INT_CREATE_INV_001"
    assert result.ast.name == "CreateInvoice"
    assert result.ast.desc == "Creates invoice for an approved order."
    assert result.ast.inputs == []
    assert result.ast.validations == []
    assert result.ast.process == []
    assert result.ast.emit == []
    assert result.ast.fail == []
    assert result.ast.return_ref is None
