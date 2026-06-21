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
    assert len(result.ast.inputs) == 2
    assert len(result.ast.process) == 4
    assert result.ast.return_spec is not None
    assert result.ast.return_spec.type == "Entity"
    assert len(result.ast.validations) == 1
    assert result.ast.metadata is not None
    assert result.ast.metadata.sla == "500ms"
