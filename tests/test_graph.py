"""Knowledge graph tests."""

from pathlib import Path

from yoni.graph.builder import build_graph
from yoni.graph.models import EdgeKind
from yoni.normalizer.run import normalize_workspace
from yoni.workspace.loader import load_workspace

FIXTURES = Path(__file__).parent / "fixtures"


def test_intent_edges() -> None:
    ws = load_workspace(FIXTURES)
    norm = normalize_workspace(ws)
    graph = build_graph(norm)
    kinds = {edge.kind for edge in graph.edges if edge.source == "INT_CREATE_INV_001"}
    assert EdgeKind.INPUT in kinds
    assert EdgeKind.VALIDATES in kinds
    assert EdgeKind.EMITS in kinds


def test_graph_json_roundtrip() -> None:
    ws = load_workspace(FIXTURES)
    norm = normalize_workspace(ws)
    graph = build_graph(norm)
    restored = graph.model_validate(graph.model_dump())
    assert len(restored.nodes) == len(graph.nodes)
    assert len(restored.edges) == len(graph.edges)


def test_domain_owns_entities() -> None:
    root = Path("samples/invoicing")
    ws = load_workspace(root)
    norm = normalize_workspace(ws)
    graph = build_graph(norm)
    owns = [
        edge
        for edge in graph.edges
        if edge.kind == EdgeKind.OWNS and edge.source == "DOM_CUSTOMER_001"
    ]
    targets = {edge.target for edge in owns}
    assert "ENT_CUSTOMER_001" in targets
