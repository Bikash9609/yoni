"""Circular dependency validation."""

from __future__ import annotations

from yoni.graph.models import EdgeKind, KnowledgeGraph
from yoni.graph.store import GraphStore
from yoni.normalizer.models import NormalizedWorkspace
from yoni.validator.codes import circular_dependency
from yoni.validator.models import ValidationError

_CYCLE_KINDS = {EdgeKind.DEPENDS_ON, EdgeKind.TRIGGERS, EdgeKind.CONSUMES}


def check_cycles(
    workspace: NormalizedWorkspace,
    graph: KnowledgeGraph,
) -> list[ValidationError]:
    store = GraphStore(graph)
    errors: list[ValidationError] = []
    seen: set[tuple[str, ...]] = set()
    for cycle in store.find_cycles(_CYCLE_KINDS):
        key = tuple(sorted(cycle))
        if key in seen:
            continue
        seen.add(key)
        block = workspace.blocks.get(cycle[0])
        errors.append(
            circular_dependency(
                cycle,
                file=block.file.rel_path if block else "",
                block_id=cycle[0],
            )
        )
    return errors
