"""Impact engine tests."""

from pathlib import Path

from yoni.graph.builder import build_graph
from yoni.impact.engine import compute_impact
from yoni.normalizer.run import normalize_workspace
from yoni.workspace.loader import load_workspace


def test_entity_impact_reaches_intents() -> None:
    root = Path("samples/invoicing")
    ws = load_workspace(root)
    norm = normalize_workspace(ws)
    graph = build_graph(norm)
    impact = compute_impact(graph, "ENT_CUSTOMER_001")
    kinds = {item.kind.value for item in impact.affected}
    assert "intent" in kinds
    assert "INT_CREATE_INV_001" in {item.id for item in impact.affected}
