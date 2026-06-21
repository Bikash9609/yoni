"""Build knowledge graph from normalized workspace."""

from __future__ import annotations

from yoni.ast.base import BlockKind
from yoni.graph.models import Edge, EdgeKind, KnowledgeGraph, Node
from yoni.normalizer.models import NormalizedRef, NormalizedWorkspace


_GLOBAL_REF_KINDS = frozenset(
    {
        "Domain",
        "Capability",
        "Project",
        "View",
        "Deployment",
        "Migration",
    }
)


def _resolve(
    workspace: NormalizedWorkspace,
    ref: NormalizedRef | dict,
    *,
    domain: str | None = None,
) -> tuple[str, bool]:
    if isinstance(ref, dict):
        kind = ref.get("kind", "")
        name = ref.get("name", "")
        raw = ref.get("raw", f"@{kind}.{name}")
        ref_obj = NormalizedRef(kind=kind, name=name, raw=raw)
    else:
        ref_obj = ref
    base = f"{ref_obj.kind}.{ref_obj.name}"
    raw = ref_obj.raw or f"@{base}"

    if ref_obj.kind in _GLOBAL_REF_KINDS:
        target = workspace.symbols.get(base)
        if target:
            return target, True
        return base, False

    if domain:
        scoped = f"{domain}:{base}"
        target = workspace.symbols.get(scoped)
        if target:
            return target, True

    target = workspace.symbols.get(base)
    if target:
        return target, True

    suffix = f":{base}"
    matches = [
        block_id
        for key, block_id in workspace.symbols.items()
        if key.endswith(suffix)
    ]
    if len(matches) == 1:
        return matches[0], True

    unresolved = f"{domain}:{base}" if domain else base
    return unresolved, False


def _add_edge(
    edges: list[Edge],
    *,
    kind: EdgeKind,
    source: str,
    ref: NormalizedRef | dict,
    workspace: NormalizedWorkspace,
    domain: str | None = None,
) -> None:
    target, resolved = _resolve(workspace, ref, domain=domain)
    raw = ref.get("raw", "") if isinstance(ref, dict) else ref.raw
    if not raw and isinstance(ref, dict):
        raw = f"@{ref.get('kind', '')}.{ref.get('name', '')}"
    edges.append(
        Edge(
            kind=kind,
            source=source,
            target=target,
            ref_raw=raw or None,
            resolved=resolved,
        )
    )


def _domain_block_for_path(workspace: NormalizedWorkspace, domain: str) -> str | None:
    for block in workspace.blocks.values():
        if block.kind != BlockKind.DOMAIN:
            continue
        if block.file.domain == domain:
            return block.block_id
    return None


def _is_ref_dict(value: object) -> bool:
    return (
        isinstance(value, dict)
        and "kind" in value
        and "name" in value
        and value.get("kind") not in {"value", "var", "call", "binary", "ref", "state_ref"}
    )


def _iter_normalized_refs(obj: object) -> list[dict]:
    refs: list[dict] = []
    if _is_ref_dict(obj):
        refs.append(obj)
        return refs
    if isinstance(obj, dict):
        if obj.get("kind") == "ref" and isinstance(obj.get("ref"), dict):
            refs.append(obj["ref"])
        for value in obj.values():
            refs.extend(_iter_normalized_refs(value))
    elif isinstance(obj, list):
        for item in obj:
            refs.extend(_iter_normalized_refs(item))
    return refs


def _add_body_refs(
    edges: list[Edge],
    *,
    source: str,
    obj: object,
    workspace: NormalizedWorkspace,
    domain: str | None,
    edge_kind: EdgeKind = EdgeKind.REFERENCES,
) -> None:
    for ref in _iter_normalized_refs(obj):
        kind = EdgeKind.TRIGGERS if ref.get("kind") == "Intent" else edge_kind
        _add_edge(
            edges,
            kind=kind,
            source=source,
            ref=ref,
            workspace=workspace,
            domain=domain,
        )


def _add_field_refs(
    edges: list[Edge],
    *,
    source: str,
    fields: list[dict],
    workspace: NormalizedWorkspace,
    domain: str | None,
) -> None:
    for field in fields:
        ref = field.get("ref")
        if ref:
            _add_edge(
                edges,
                kind=EdgeKind.REFERENCES,
                source=source,
                ref=ref,
                workspace=workspace,
                domain=domain,
            )


def _add_env_refs(
    edges: list[Edge],
    *,
    source: str,
    env: dict | None,
    workspace: NormalizedWorkspace,
    domain: str | None,
) -> None:
    if not env:
        return
    for value in env.get("entries", {}).values():
        if _is_ref_dict(value):
            _add_edge(
                edges,
                kind=EdgeKind.REFERENCES,
                source=source,
                ref=value,
                workspace=workspace,
                domain=domain,
            )


def build_graph(workspace: NormalizedWorkspace) -> KnowledgeGraph:
    nodes: dict[str, Node] = {}
    edges: list[Edge] = []

    for block_id, block in workspace.blocks.items():
        nodes[block_id] = Node(
            id=block_id,
            kind=block.kind,
            name=block.name,
            version=block.version,
            file=block.file.rel_path,
            domain=block.file.domain,
            ast_ref=block.ast_ref,
        )

    for block_id, block in workspace.blocks.items():
        body = block.body
        kind = block.kind
        domain = block.file.domain

        if kind == BlockKind.PROJECT:
            for ref in body.get("domains", []):
                _add_edge(edges, kind=EdgeKind.OWNS, source=block_id, ref=ref, workspace=workspace)
            for ref in body.get("capabilities", []):
                _add_edge(edges, kind=EdgeKind.OWNS, source=block_id, ref=ref, workspace=workspace)
            _add_env_refs(
                edges,
                source=block_id,
                env=body.get("env"),
                workspace=workspace,
                domain=domain,
            )

        elif kind == BlockKind.DOMAIN:
            for key, edge_kind in (
                ("entities", EdgeKind.OWNS),
                ("rules", EdgeKind.OWNS),
                ("events", EdgeKind.OWNS),
            ):
                for ref in body.get(key, []):
                    _add_edge(
                        edges,
                        kind=edge_kind,
                        source=block_id,
                        ref=ref,
                        workspace=workspace,
                        domain=domain,
                    )

        elif kind == BlockKind.INTENT:
            for field in body.get("inputs", []):
                ref = field.get("ref")
                if ref:
                    _add_edge(
                        edges,
                        kind=EdgeKind.INPUT,
                        source=block_id,
                        ref=ref,
                        workspace=workspace,
                        domain=domain,
                    )
            for ref in body.get("validations", []):
                _add_edge(
                    edges,
                    kind=EdgeKind.VALIDATES,
                    source=block_id,
                    ref=ref,
                    workspace=workspace,
                    domain=domain,
                )
            for ref in body.get("emit", []):
                _add_edge(
                    edges,
                    kind=EdgeKind.EMITS,
                    source=block_id,
                    ref=ref,
                    workspace=workspace,
                    domain=domain,
                )
            for ref in body.get("fail", []):
                _add_edge(
                    edges,
                    kind=EdgeKind.FAILS,
                    source=block_id,
                    ref=ref,
                    workspace=workspace,
                    domain=domain,
                )
            for step in body.get("process", []):
                type_ref = step.get("type_ref")
                if step.get("op") == "new" and type_ref:
                    _add_edge(
                        edges,
                        kind=EdgeKind.OUTPUT,
                        source=block_id,
                        ref=type_ref,
                        workspace=workspace,
                        domain=domain,
                    )
            ret = body.get("return")
            if ret:
                _add_edge(
                    edges,
                    kind=EdgeKind.OUTPUT,
                    source=block_id,
                    ref=ret,
                    workspace=workspace,
                    domain=domain,
                )

        elif kind == BlockKind.QUERY:
            entity = body.get("entity")
            if entity:
                _add_edge(
                    edges,
                    kind=EdgeKind.REFERENCES,
                    source=block_id,
                    ref=entity,
                    workspace=workspace,
                    domain=domain,
                )

        elif kind == BlockKind.ACTION:
            uses = body.get("uses")
            if uses:
                _add_edge(
                    edges,
                    kind=EdgeKind.USES,
                    source=block_id,
                    ref=uses,
                    workspace=workspace,
                    domain=domain,
                )
            _add_field_refs(
                edges,
                source=block_id,
                fields=body.get("inputs", []) + body.get("result", []),
                workspace=workspace,
                domain=domain,
            )

        elif kind == BlockKind.ENTITY:
            _add_field_refs(
                edges,
                source=block_id,
                fields=body.get("fields", []),
                workspace=workspace,
                domain=domain,
            )

        elif kind == BlockKind.RULE:
            _add_body_refs(
                edges,
                source=block_id,
                obj=body.get("expression"),
                workspace=workspace,
                domain=domain,
                edge_kind=EdgeKind.REFERENCES,
            )

        elif kind == BlockKind.EVENT:
            _add_field_refs(
                edges,
                source=block_id,
                fields=body.get("payload", []),
                workspace=workspace,
                domain=domain,
            )

        elif kind == BlockKind.VIEW:
            query = body.get("query")
            if query:
                _add_edge(
                    edges,
                    kind=EdgeKind.USES,
                    source=block_id,
                    ref=query,
                    workspace=workspace,
                    domain=domain,
                )
            for ref in body.get("actions", []):
                _add_edge(
                    edges,
                    kind=EdgeKind.REFERENCES,
                    source=block_id,
                    ref=ref,
                    workspace=workspace,
                    domain=domain,
                )

        elif kind == BlockKind.WORKFLOW:
            for step in body.get("steps", []):
                intent = step.get("intent")
                if intent:
                    _add_edge(
                        edges,
                        kind=EdgeKind.DEPENDS_ON,
                        source=block_id,
                        ref=intent,
                        workspace=workspace,
                        domain=domain,
                    )
                for inp in step.get("inputs", []):
                    value = inp.get("value")
                    if isinstance(value, dict) and value.get("kind") == "ref":
                        _add_edge(
                            edges,
                            kind=EdgeKind.CONSUMES,
                            source=block_id,
                            ref=value["ref"],
                            workspace=workspace,
                            domain=domain,
                        )
                    elif isinstance(value, dict) and "ref" in value:
                        ref_val = value.get("ref")
                        if isinstance(ref_val, dict):
                            _add_edge(
                                edges,
                                kind=EdgeKind.CONSUMES,
                                source=block_id,
                                ref=ref_val,
                                workspace=workspace,
                                domain=domain,
                            )

        elif kind == BlockKind.TEST:
            when = body.get("when") or {}
            intent = when.get("intent")
            if intent:
                _add_edge(
                    edges,
                    kind=EdgeKind.TRIGGERS,
                    source=block_id,
                    ref=intent,
                    workspace=workspace,
                    domain=domain,
                )
            for expect in body.get("expect", []):
                event = expect.get("event")
                if event:
                    _add_edge(
                        edges,
                        kind=EdgeKind.REFERENCES,
                        source=block_id,
                        ref=event,
                        workspace=workspace,
                        domain=domain,
                    )

        elif kind == BlockKind.CONSTRAINT:
            entity = body.get("entity")
            if entity:
                _add_edge(
                    edges,
                    kind=EdgeKind.REFERENCES,
                    source=block_id,
                    ref=entity,
                    workspace=workspace,
                    domain=domain,
                )

        elif kind == BlockKind.MIGRATION:
            for change in body.get("changes", []):
                entity = change.get("entity")
                if entity:
                    _add_edge(
                        edges,
                        kind=EdgeKind.DEPENDS_ON,
                        source=block_id,
                        ref=entity,
                        workspace=workspace,
                        domain=domain,
                    )
            for ref in body.get("affects", []):
                _add_edge(
                    edges,
                    kind=EdgeKind.REFERENCES,
                    source=block_id,
                    ref=ref,
                    workspace=workspace,
                    domain=domain,
                )

        elif kind == BlockKind.CAPABILITY:
            for ref in body.get("actions", []):
                _add_edge(
                    edges,
                    kind=EdgeKind.REFERENCES,
                    source=block_id,
                    ref=ref,
                    workspace=workspace,
                    domain=domain,
                )

        elif kind == BlockKind.DEPLOYMENT:
            for ref in body.get("services", []):
                _add_edge(
                    edges,
                    kind=EdgeKind.REFERENCES,
                    source=block_id,
                    ref=ref,
                    workspace=workspace,
                    domain=domain,
                )
            _add_env_refs(
                edges,
                source=block_id,
                env=body.get("env"),
                workspace=workspace,
                domain=domain,
            )

        if block.file.domain and kind not in (BlockKind.DOMAIN, BlockKind.PROJECT):
            domain_id = _domain_block_for_path(workspace, block.file.domain)
            if domain_id:
                edges.append(
                    Edge(
                        kind=EdgeKind.OWNS,
                        source=domain_id,
                        target=block_id,
                        ref_raw=None,
                        resolved=True,
                    )
                )

    return KnowledgeGraph(nodes=nodes, edges=edges)
