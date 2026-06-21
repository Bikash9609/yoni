"""Canonical ordering, field sorting, ref resolution, and emit."""

from __future__ import annotations

from typing import Any

from yoni.ast.base import BlockKind
from yoni.normalizer.models import NormalizedWorkspace

_SECTION_ORDER: dict[BlockKind, tuple[str, ...]] = {
    BlockKind.ENTITY: ("fields", "indices"),
    BlockKind.INTENT: ("inputs", "validations", "process", "emit", "fail", "return", "metadata"),
    BlockKind.QUERY: ("entity", "where", "order_by", "limit", "return"),
    BlockKind.ACTION: ("uses", "inputs", "result"),
    BlockKind.STATE: ("states", "transitions"),
    BlockKind.EVENT: ("payload",),
    BlockKind.WORKFLOW: ("steps",),
    BlockKind.RULE: ("expression",),
    BlockKind.CONSTRAINT: ("entity", "check"),
    BlockKind.ERROR: ("code", "http_status", "message"),
    BlockKind.TEST: ("given", "when", "expect"),
    BlockKind.CAPABILITY: ("actions", "config"),
    BlockKind.VIEW: ("query", "fields", "actions", "layout"),
    BlockKind.PROJECT: ("domains", "capabilities", "env"),
    BlockKind.DOMAIN: ("entities", "rules", "events"),
    BlockKind.DEPLOYMENT: ("region", "replicas", "resources", "services", "env"),
    BlockKind.MIGRATION: ("from_version", "to_version", "breaking", "changes", "affects"),
}


def sort_fields(fields: list[Any]) -> list[Any]:
    if not fields:
        return fields
    if isinstance(fields[0], str):
        return sorted(fields)
    return sorted(fields, key=lambda f: f.get("name", "") if isinstance(f, dict) else str(f))


def order_body(kind: BlockKind, body: dict[str, Any]) -> dict[str, Any]:
    order = _SECTION_ORDER.get(kind, ())
    ordered: dict[str, Any] = {}
    for key in order:
        if key not in body:
            continue
        value = body[key]
        if key in {"fields", "inputs", "payload", "config", "result"} and isinstance(value, list):
            ordered[key] = sort_fields(value)
        else:
            ordered[key] = value
    for key, value in body.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def resolve_ref_dict(
    ref: dict[str, Any],
    workspace: NormalizedWorkspace,
    *,
    domain: str | None,
) -> dict[str, Any]:
    from yoni.normalizer.models import NormalizedRef

    nr = NormalizedRef(
        kind=ref.get("kind", ""),
        name=ref.get("name", ""),
        raw=ref.get("raw", ""),
        path=list(ref.get("path", [])),
    )
    block_id = workspace.resolve(nr, domain=domain)
    out = dict(ref)
    if block_id:
        out["block_id"] = block_id
    return out


def resolve_refs_in_value(
    value: Any,
    workspace: NormalizedWorkspace,
    *,
    domain: str | None,
) -> Any:
    if isinstance(value, dict):
        if "kind" in value and "name" in value and "block_id" not in value:
            if value.get("kind") not in {"var", "value", "binary", "call", "ref", "state_ref"}:
                return resolve_ref_dict(value, workspace, domain=domain)
        if value.get("kind") == "ref" and isinstance(value.get("ref"), dict):
            resolved = dict(value)
            resolved["ref"] = resolve_ref_dict(value["ref"], workspace, domain=domain)
            return resolved
        return {
            key: resolve_refs_in_value(item, workspace, domain=domain)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [resolve_refs_in_value(item, workspace, domain=domain) for item in value]
    return value


def resolve_body_refs(
    body: dict[str, Any],
    workspace: NormalizedWorkspace,
    *,
    domain: str | None,
) -> dict[str, Any]:
    return resolve_refs_in_value(body, workspace, domain=domain)


def normalize_indent(source: str) -> str:
    lines = source.replace("\t", "  ").splitlines()
    out: list[str] = []
    for line in lines:
        stripped = line.lstrip(" ")
        depth = len(line) - len(stripped)
        out.append(" " * (depth - depth % 2) + stripped)
    return "\n".join(out) + ("\n" if source.endswith("\n") else "")


def emit_canonical(
    *,
    kind: BlockKind,
    name: str,
    block_id: str,
    desc: str,
    body: dict[str, Any],
) -> str:
    """Render canonical Yoni text from a normalized block."""
    lines = [f"{kind.value} {name}", "", f"id: {block_id}", "desc:"]
    if desc.strip():
        lines.append(f"  {desc.strip()}")
    lines.append("")
    for section, value in body.items():
        if section == "metadata" or value is None:
            continue
        if section in {"inputs", "validations", "process", "emit", "fail"}:
            key = {
                "inputs": "input",
                "validations": "validate",
            }.get(section, section)
            lines.extend(_emit_section(key, value))
            continue
        if section == "expression":
            lines.extend(_emit_section("expression", value))
            continue
        lines.extend(_emit_section(section, value))
    return "\n".join(lines) + "\n"


def _emit_section(key: str, value: Any) -> list[str]:
    if isinstance(value, list):
        if not value:
            return [f"{key}:", ""]
        out = [f"{key}:"]
        for item in value:
            out.append(f"  {_emit_line(item)}")
        out.append("")
        return out
    if isinstance(value, dict):
        if key in {"entity", "uses", "query", "return"} and "raw" in value:
            return [f"{key}: {value.get('raw', '')}", ""]
        if key == "where" or key == "check":
            return [f"{key}:", f"  {_emit_expr(value)}", ""]
        return [f"{key}:", ""]
    return [f"{key}: {value}", ""]


def _emit_line(item: Any) -> str:
    if isinstance(item, dict):
        if "name" in item and "type_code" in item:
            tc = item.get("type_code") or "s"
            mods = []
            if item.get("unique"):
                mods.append("unique")
            if item.get("nullable"):
                mods.append("nullable")
            suffix = " " + " ".join(mods) if mods else ""
            return f"{item['name']}: {tc}{suffix}"
        if "ref" in item:
            ref = item["ref"]
            if isinstance(ref, dict):
                return ref.get("raw", "")
            return str(ref)
        if item.get("op"):
            return _emit_process(item)
        if "step" in item and "intent" in item:
            return f"{item['step']}: {item['intent'].get('raw', '')}"
    return str(item)


def _emit_process(item: dict[str, Any]) -> str:
    op = item.get("op", "")
    if op == "new":
        tr = item.get("type_ref") or {}
        return f"new {item.get('target', '')} {tr.get('raw', '')}"
    if op == "set":
        return f"set {item.get('target', '')} {item.get('value', '')}"
    if op == "save":
        return f"save {item.get('target', '')}"
    return str(item)


def _emit_expr(node: dict[str, Any] | None) -> str:
    if not node:
        return ""
    kind = node.get("kind")
    if kind == "binary":
        return f"{_emit_expr(node.get('left'))} {node.get('op')} {_emit_expr(node.get('right'))}"
    if kind == "var":
        return node.get("name", "")
    if kind == "value":
        return str(node.get("value", ""))
    if kind == "ref":
        ref = node.get("ref") or {}
        return ref.get("raw", "")
    return str(node)
