"""Deep AST tests for migration blocks."""

from pathlib import Path

from yoni import parse_file, parse_source
from yoni.ast.migration import MigrationAST

FIXTURES = Path(__file__).parent / "fixtures"


def test_migration_add_field() -> None:
    result = parse_file(FIXTURES / "migration_customer_v2.yoni")
    assert result.ok, result.errors
    assert isinstance(result.ast, MigrationAST)
    assert result.ast.from_version == 1
    assert result.ast.to_version == 2
    assert result.ast.breaking is False
    assert len(result.ast.changes) == 1
    change = result.ast.changes[0]
    assert change.change_type == "AddField"
    assert change.field is not None
    assert change.field.name == "phone"
    assert change.field.type_code == "s"
    assert change.field.type == "string"
    assert change.field.nullable is True


def test_migration_all_change_types() -> None:
    source = """migration AllChanges

id: MIG_ALL_001
desc:
  All change types.

from_version: 1
to_version: 2
breaking: false
changes:
  AddField @Entity.Customer phone s
  RemoveField @Entity.Customer age
  RenameField @Entity.Customer email primary_email
  ReplaceReference @Entity.Customer @Entity.Account
  CreateTransition Draft -> Paid
  RemoveTransition Draft -> Cancelled
"""
    result = parse_source(source)
    assert result.ok, result.errors
    types = [c.change_type for c in result.ast.changes]
    assert types == [
        "AddField",
        "RemoveField",
        "RenameField",
        "ReplaceReference",
        "CreateTransition",
        "RemoveTransition",
    ]
