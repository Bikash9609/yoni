"""Smoke tests for entity block parsing."""

from pathlib import Path

from yoni import parse_file
from yoni.ast.entity import EntityAST
from yoni.ast.types import TypeCode

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_entity_customer() -> None:
    result = parse_file(FIXTURES / "entity_customer.yoni")
    assert result.ok, result.errors
    assert isinstance(result.ast, EntityAST)
    assert result.ast.id == "ENT_CUSTOMER_001"
    assert result.ast.name == "Customer"
    assert result.ast.desc == "Primary customer record."
    assert len(result.ast.fields) == 3
    assert result.ast.fields[0].name == "customer_id"
    assert result.ast.fields[0].type_code == TypeCode.STRING
    assert result.ast.fields[1].name == "email"
    assert result.ast.fields[2].name == "active"
    assert result.ast.fields[2].type_code == TypeCode.BOOLEAN
