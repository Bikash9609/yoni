"""Migration evolution validation."""

from __future__ import annotations

from yoni.ast.base import BlockKind
from yoni.normalizer.models import NormalizedRef, NormalizedWorkspace
from yoni.validator.codes import breaking_migration_incomplete, breaking_change_without_migration
from yoni.validator.models import ValidationError


def _resolve_body_ref(
    workspace: NormalizedWorkspace,
    ref: dict | None,
    *,
    domain: str | None,
) -> str | None:
    if not ref or not isinstance(ref, dict):
        return None
    return workspace.resolve(
        NormalizedRef(
            kind=str(ref.get("kind", "")),
            name=str(ref.get("name", "")),
            raw=str(ref.get("raw", "")),
        ),
        domain=domain,
    )


def check_evolution(workspace: NormalizedWorkspace) -> list[ValidationError]:
    errors: list[ValidationError] = []
    migrated: set[str] = set()

    for block in workspace.blocks.values():
        if block.kind != BlockKind.MIGRATION:
            continue
        if block.body.get("breaking") and (
            not block.body.get("changes") or not block.body.get("affects")
        ):
            errors.append(
                breaking_migration_incomplete(
                    block.block_id,
                    file=block.file.rel_path,
                )
            )
        for ref in block.body.get("affects", []):
            target = _resolve_body_ref(workspace, ref, domain=block.file.domain)
            if target:
                migrated.add(target)
        for change in block.body.get("changes", []):
            target = _resolve_body_ref(workspace, change.get("entity"), domain=block.file.domain)
            if target:
                migrated.add(target)

    versioned_kinds = {BlockKind.ENTITY, BlockKind.STATE}
    for block in workspace.blocks.values():
        if block.kind not in versioned_kinds or block.version <= 1:
            continue
        if block.block_id not in migrated:
            errors.append(
                breaking_change_without_migration(
                    block.block_id,
                    file=block.file.rel_path,
                )
            )
    return errors
