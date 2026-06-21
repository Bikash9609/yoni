"""Section validation and desc required tests."""

from yoni import parse_source


def test_missing_desc() -> None:
    source = """entity Customer

id: ENT_001

fields:
  id: s
"""
    result = parse_source(source)
    assert result.ok, result.errors
    assert result.ast.desc == ""


def test_unknown_section() -> None:
    source = """entity Customer

id: ENT_001
desc:
  Has unknown section.

bogus:
  customer_id
"""
    result = parse_source(source)
    assert not result.ok or any(e.code == "YONI1005" for e in result.errors)


def test_duplicate_section() -> None:
    source = """entity Customer

id: ENT_001
desc:
  Duplicate fields.

fields:
  a: s
fields:
  b: s
"""
    result = parse_source(source)
    assert any(e.code == "YONI1009" for e in result.errors)


def test_tab_rejection() -> None:
    source = "entity Customer\n\nid: ENT_001\ndesc:\n\tTab indented.\n"
    result = parse_source(source)
    assert any(e.code == "YONI1008" for e in result.errors)
