"""Deep AST tests for query blocks."""

from pathlib import Path

from yoni import parse_file, parse_source
from yoni.ast.expr import ExprBinary, ExprValue, ExprVar
from yoni.ast.query import QueryAST

FIXTURES = Path(__file__).parent / "fixtures"


def test_query_where_order_by_return_list() -> None:
    result = parse_file(FIXTURES / "query_active_customers.yoni")
    assert result.ok, result.errors
    assert isinstance(result.ast, QueryAST)
    assert result.ast.entity is not None
    assert result.ast.entity.ref.kind == "Entity"
    where = result.ast.where
    assert isinstance(where, ExprBinary)
    assert isinstance(where.left, ExprVar)
    assert isinstance(where.right, ExprValue)
    assert len(result.ast.order_by) == 1
    assert result.ast.order_by[0].field == "created_at"
    assert result.ast.order_by[0].direction == "desc"
    assert result.ast.limit == 100
    assert result.ast.return_spec is not None
    assert result.ast.return_spec.type == "list"
    assert result.ast.return_spec.inner is not None


def test_query_return_section() -> None:
    source = """query Items

id: QUERY_ITEMS_001
desc:
  List return via section.

entity: @Entity.Customer
where:
  active == true
return:
  list[@Entity.Customer]
"""
    result = parse_source(source)
    assert result.ok, result.errors
    assert result.ast.return_spec.type == "list"
