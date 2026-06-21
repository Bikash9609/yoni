"""Normalizer tests."""

from pathlib import Path

from yoni.normalizer.run import normalize_workspace
from yoni.workspace.loader import load_workspace

FIXTURES = Path(__file__).parent / "fixtures"


def test_normalize_entity_defaults() -> None:
    ws = load_workspace(FIXTURES)
    norm = normalize_workspace(ws)
    block = norm.blocks["ENT_CUSTOMER_001"]
    assert block.kind.value == "entity"
    field = next(f for f in block.body["fields"] if f["name"] == "customer_id")
    assert field["type"] == "string"
    assert field["nullable"] is False


def test_symbol_table() -> None:
    ws = load_workspace(FIXTURES)
    norm = normalize_workspace(ws)
    assert norm.symbols["Entity.Customer"] == "ENT_CUSTOMER_001"
    assert norm.symbols["Intent.CreateInvoice"] == "INT_CREATE_INV_001"


def test_domain_scoped_symbol() -> None:
    root = Path("samples/invoicing")
    ws = load_workspace(root)
    norm = normalize_workspace(ws)
    assert norm.symbols["customer:Entity.Customer"] == "ENT_CUSTOMER_001"
    assert norm.symbols["Domain.Customer"] == "DOM_CUSTOMER_001"
