"""Extract references from AST values."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from yoni.ast.types import FieldDef, RefLink, Reference
from yoni.normalizer.expr import ref_from_reference
from yoni.normalizer.models import NormalizedRef


def _collect_from_value(value: Any, refs: list[NormalizedRef], *, role: str | None) -> None:
    if value is None:
        return
    if isinstance(value, Reference):
        refs.append(ref_from_reference(value, role=role))
        return
    if isinstance(value, RefLink):
        refs.append(ref_from_reference(value.ref, role=role))
        return
    if isinstance(value, FieldDef) and value.ref is not None:
        refs.append(ref_from_reference(value.ref, role=role or "field"))
        return
    if isinstance(value, BaseModel):
        for field_name, field_value in value:
            _collect_from_value(field_value, refs, role=role or field_name)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _collect_from_value(item, refs, role=role or str(key))
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _collect_from_value(item, refs, role=role)
        return
    if isinstance(value, str) and value.startswith("@"):
        try:
            refs.append(ref_from_reference(Reference.parse(value), role=role))
        except ValueError:
            pass


def extract_refs(ast: BaseModel) -> list[NormalizedRef]:
    refs: list[NormalizedRef] = []
    _collect_from_value(ast, refs, role=None)
    seen: set[tuple[str, str, str]] = set()
    unique: list[NormalizedRef] = []
    for ref in refs:
        key = (ref.kind, ref.name, ref.raw)
        if key in seen:
            continue
        seen.add(key)
        unique.append(ref)
    return unique
