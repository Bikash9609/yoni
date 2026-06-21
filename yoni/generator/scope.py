"""Scope resolution — user request intersected with graph closure."""

from __future__ import annotations

from yoni.ast.base import BlockKind
from yoni.generator.errors import GenerateError
from yoni.generator.models import GenerationLayer, ResolvedScope, ScopeRequest
from yoni.graph.models import KnowledgeGraph
from yoni.graph.store import GraphStore
from yoni.normalizer.models import NormalizedWorkspace
from yoni.planner.models import JobType

_JOB_LAYERS: dict[JobType, frozenset[GenerationLayer]] = {
    JobType.ENTITY_SCHEMA: frozenset({GenerationLayer.BACKEND}),
    JobType.STATE_MACHINE: frozenset({GenerationLayer.BACKEND}),
    JobType.ERROR_DEF: frozenset({GenerationLayer.BACKEND}),
    JobType.RULE_IMPL: frozenset({GenerationLayer.BACKEND}),
    JobType.CONSTRAINT_IMPL: frozenset({GenerationLayer.BACKEND}),
    JobType.QUERY_IMPL: frozenset({GenerationLayer.BACKEND}),
    JobType.ACTION_IMPL: frozenset({GenerationLayer.BACKEND}),
    JobType.INTENT_HANDLER: frozenset({GenerationLayer.BACKEND}),
}


def resolve_scope(
    workspace: NormalizedWorkspace,
    graph: KnowledgeGraph,
    scope: ScopeRequest,
) -> ResolvedScope:
    """Resolve user targets to intent ids and a forward graph closure."""
    if not scope.targets:
        raise GenerateError(
            "YONI5001",
            "No generation targets provided",
            suggestion="Pass --intent, --domain, or --targets.",
        )

    intent_ids = _resolve_targets(workspace, graph, scope.targets)
    store = GraphStore(graph)
    block_closure = store.forward_closure(intent_ids)

    return ResolvedScope(
        targets=list(scope.targets),
        intent_ids=sorted(intent_ids),
        block_closure=block_closure,
        layers=list(scope.layers),
        stack=scope.stack,
    )


def job_allowed_for_layers(job_type: JobType, layers: list[GenerationLayer]) -> bool:
    allowed = _JOB_LAYERS.get(job_type, frozenset({GenerationLayer.BACKEND}))
    layer_set = set(layers)
    return bool(allowed & layer_set)


def block_in_closure(block_id: str, resolved: ResolvedScope) -> bool:
    return block_id in resolved.block_closure


def _resolve_targets(
    workspace: NormalizedWorkspace,
    graph: KnowledgeGraph,
    targets: list[str],
) -> list[str]:
    intent_ids: list[str] = []
    seen: set[str] = set()

    for raw in targets:
        token = raw.strip()
        if not token:
            continue

        for intent_id in _resolve_single_target(workspace, graph, token):
            if intent_id not in seen:
                seen.add(intent_id)
                intent_ids.append(intent_id)

    if not intent_ids:
        raise GenerateError(
            "YONI5002",
            f"No intents resolved from targets: {targets!r}",
            suggestion="Use valid intent block ids (INT_*) or domain names.",
        )
    return intent_ids


def _resolve_single_target(
    workspace: NormalizedWorkspace,
    graph: KnowledgeGraph,
    token: str,
) -> list[str]:
    block_id = token.upper()
    if block_id in workspace.blocks:
        block = workspace.blocks[block_id]
        if block.kind == BlockKind.INTENT:
            return [block_id]
        if block.kind == BlockKind.DOMAIN:
            domain_name = block.name.lower()
            intents = _intents_for_domain(workspace, domain_name)
            if intents:
                return intents
            raise GenerateError(
                "YONI5003",
                f"Domain block {block_id!r} has no intents",
                block_id=block_id,
                suggestion="Add intents under this domain or target an intent directly.",
            )
        raise GenerateError(
            "YONI5004",
            f"Target {block_id!r} is {block.kind.value}, not intent or domain",
            block_id=block_id,
            suggestion="Target intent (INT_*) or domain blocks only.",
        )

    if block_id in graph.nodes:
        node = graph.nodes[block_id]
        if node.kind == BlockKind.INTENT:
            return [block_id]
        raise GenerateError(
            "YONI5004",
            f"Target {block_id!r} is {node.kind.value}, not intent or domain",
            block_id=block_id,
            suggestion="Target intent (INT_*) or domain blocks only.",
        )

    domain_name = token.lower()
    intents = _intents_for_domain(workspace, domain_name)
    if intents:
        return intents

    raise GenerateError(
        "YONI5005",
        f"Unknown target {token!r}",
        suggestion="Use a valid block id or domain folder name.",
    )


def _intents_for_domain(
    workspace: NormalizedWorkspace,
    domain_name: str,
) -> list[str]:
    intents: list[str] = []
    for block_id, block in sorted(workspace.blocks.items()):
        if block.kind != BlockKind.INTENT:
            continue
        if block.file.domain == domain_name:
            intents.append(block_id)
    return intents
