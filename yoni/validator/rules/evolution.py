"""Migration evolution validation."""

from __future__ import annotations

from yoni.ast.base import BlockKind
from yoni.normalizer.models import NormalizedWorkspace
from yoni.validator.codes import breaking_migration_incomplete
from yoni.validator.models import ValidationError


def check_evolution(workspace: NormalizedWorkspace) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for block in workspace.blocks.values():
        if block.kind != BlockKind.MIGRATION:
            continue
        if not block.body.get("breaking"):
            continue
        if not block.body.get("changes") or not block.body.get("affects"):
            errors.append(
                breaking_migration_incomplete(
                    block.block_id,
                    file=block.file.rel_path,
                )
            )
    return errors
