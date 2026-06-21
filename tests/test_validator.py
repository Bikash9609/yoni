"""Validator tests."""

from pathlib import Path

from yoni import parse_source
from yoni.graph.builder import build_graph
from yoni.normalizer.run import normalize_workspace
from yoni.validator.run import validate_workspace
from yoni.workspace.loader import Workspace, load_workspace

FIXTURES = Path(__file__).parent / "fixtures"


def test_invoicing_validates_clean() -> None:
    ws = load_workspace("samples/invoicing")
    norm = normalize_workspace(ws)
    graph = build_graph(norm)
    errors = validate_workspace(norm, graph, ws)
    assert not [e for e in errors if e.severity == "error"]


def test_unresolved_reference_yoni2001() -> None:
    source = """query Bad

id: QUERY_BAD_001
desc:
  Bad entity reference.

entity: @Entity.Missing

where:
  active == true
"""
    result = parse_source(source, file="domains/test/queries/bad.yoni")
    assert result.ok, result.errors
    from yoni.workspace.loader import ParsedFile

    ws = Workspace(
        root=".",
        files=[
            ParsedFile(
                rel_path="domains/test/queries/bad.yoni",
                abs_path="bad.yoni",
                result=result,
            )
        ],
    )
    norm = normalize_workspace(ws)
    graph = build_graph(norm)
    errors = validate_workspace(norm, graph, ws)
    assert any(e.code == "YONI2001" for e in errors)


def test_wrong_id_prefix_yoni2004() -> None:
    source = """entity Customer

id: BAD_CUSTOMER_001
desc:
  Wrong prefix.

fields:
  id: s
"""
    result = parse_source(source, file="domains/customer/entities/customer.yoni")
    assert result.ok
    from yoni.workspace.loader import ParsedFile

    ws = Workspace(
        root=".",
        files=[
            ParsedFile(
                rel_path="domains/customer/entities/customer.yoni",
                abs_path="customer.yoni",
                result=result,
            )
        ],
    )
    norm = normalize_workspace(ws)
    graph = build_graph(norm)
    errors = validate_workspace(norm, graph, ws)
    assert any(e.code == "YONI2004" for e in errors)
