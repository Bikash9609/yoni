"""Canonical expression normalization."""

from __future__ import annotations

from typing import Any

from yoni.ast.expr import (
    ExprBinary,
    ExprCall,
    ExprNode,
    ExprRef,
    ExprValue,
    ExprVar,
    ProcessOp,
)
from yoni.ast.types import Reference
from yoni.normalizer.models import NormalizedRef


def ref_from_reference(ref: Reference, *, role: str | None = None) -> NormalizedRef:
    return NormalizedRef(
        kind=ref.kind,
        name=ref.name,
        raw=ref.raw,
        path=list(ref.path),
        role=role,
    )


def normalize_expr(node: ExprNode | None) -> dict[str, Any] | None:
    if node is None:
        return None
    if isinstance(node, ExprVar):
        return {"kind": "var", "name": node.name}
    if isinstance(node, ExprValue):
        return {"kind": "value", "value": node.value, "type": node.type}
    if isinstance(node, ExprRef):
        return {
            "kind": "ref",
            "ref": ref_from_reference(node.ref).model_dump(),
        }
    if isinstance(node, ExprCall):
        return {
            "kind": "call",
            "op": node.op,
            "args": [normalize_expr(arg) for arg in node.args],
        }
    if isinstance(node, ExprBinary):
        return {
            "kind": "binary",
            "op": node.op,
            "left": normalize_expr(node.left),
            "right": normalize_expr(node.right),
        }
    return None


def normalize_process_value(value: Any) -> Any:
    if isinstance(value, Reference):
        return ref_from_reference(value, role="process").model_dump()
    if isinstance(value, str) and "." in value and value.split(".")[0].isupper():
        left, _, right = value.partition(".")
        if left.startswith(("STS_", "ENT_", "INT_", "EVT_")):
            return {"kind": "state_ref", "state_id": left, "state_name": right}
    if isinstance(value, (ExprVar, ExprValue, ExprRef, ExprCall, ExprBinary)):
        return normalize_expr(value)
    return value


def normalize_process_op(op: ProcessOp) -> dict[str, Any]:
    payload: dict[str, Any] = {"op": op.op}
    if op.target is not None:
        payload["target"] = op.target
    if op.type_ref is not None:
        payload["type_ref"] = ref_from_reference(op.type_ref, role="process").model_dump()
    if op.value is not None:
        payload["value"] = normalize_process_value(op.value)
    return payload
