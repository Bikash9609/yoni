"""Compute downstream impact for a block change."""

from __future__ import annotations

from pydantic import BaseModel, Field

from yoni.ast.base import BlockKind
from yoni.graph.models import KnowledgeGraph
from yoni.graph.store import GraphStore


class ImpactedBlock(BaseModel):
    id: str
    kind: BlockKind
    name: str
    file: str


class ImpactResult(BaseModel):
    block_id: str
    affected: list[ImpactedBlock] = Field(default_factory=list)
    by_kind: dict[str, list[str]] = Field(default_factory=dict)


def compute_impact(graph: KnowledgeGraph, block_id: str) -> ImpactResult:
    store = GraphStore(graph)
    if block_id not in graph.nodes:
        return ImpactResult(block_id=block_id)

    impacted_ids = store.reverse_reachable(block_id)
    affected: list[ImpactedBlock] = []
    by_kind: dict[str, list[str]] = {}

    for node_id in sorted(impacted_ids):
        node = graph.nodes[node_id]
        affected.append(
            ImpactedBlock(
                id=node.id,
                kind=node.kind,
                name=node.name,
                file=node.file,
            )
        )
        key = node.kind.value
        by_kind.setdefault(key, []).append(node.id)

    return ImpactResult(block_id=block_id, affected=affected, by_kind=by_kind)
