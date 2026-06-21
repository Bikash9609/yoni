"""GraphStore forward closure tests."""

from pathlib import Path

from yoni.graph.builder import build_graph
from yoni.graph.store import GraphStore
from yoni.normalizer.run import normalize_workspace
from yoni.workspace.loader import load_workspace


def test_descendants_from_intent() -> None:
    root = Path("samples/invoicing")
    norm = normalize_workspace(load_workspace(root))
    graph = build_graph(norm)
    store = GraphStore(graph)

    descendants = store.descendants("INT_REGISTER_USER_001")
    assert "ENT_CUSTOMER_001" in descendants
    assert "RULE_ADULT_001" in descendants


def test_forward_reachable_includes_seed() -> None:
    root = Path("samples/invoicing")
    norm = normalize_workspace(load_workspace(root))
    graph = build_graph(norm)
    store = GraphStore(graph)

    reachable = store.forward_reachable("INT_REGISTER_USER_001")
    assert "INT_REGISTER_USER_001" in reachable
    assert "ENT_CUSTOMER_001" in reachable


def test_forward_closure_multiple_seeds() -> None:
    root = Path("samples/invoicing")
    norm = normalize_workspace(load_workspace(root))
    graph = build_graph(norm)
    store = GraphStore(graph)

    closure = store.forward_closure(
        ["INT_REGISTER_USER_001", "INT_CREATE_INV_001"],
    )
    assert "ENT_CUSTOMER_001" in closure
    assert "INT_REGISTER_USER_001" in closure
    assert "INT_CREATE_INV_001" in closure
