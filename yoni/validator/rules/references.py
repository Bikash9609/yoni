"""Unresolved reference validation."""

from __future__ import annotations

from yoni.graph.models import KnowledgeGraph
from yoni.normalizer.models import NormalizedWorkspace
from yoni.validator.codes import unresolved_reference
from yoni.validator.models import ValidationError


def check_references(
    workspace: NormalizedWorkspace,
    graph: KnowledgeGraph,
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for edge in graph.edges:
        if edge.resolved:
            continue
        block = workspace.blocks.get(edge.source)
        errors.append(
            unresolved_reference(
                edge.ref_raw or edge.target,
                file=block.file.rel_path if block else "",
                block_id=edge.source,
            )
        )
    return errors
