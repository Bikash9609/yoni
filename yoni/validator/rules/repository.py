"""Repository folder placement validation."""

from __future__ import annotations

from yoni.ast.base import BlockKind
from yoni.normalizer.models import NormalizedWorkspace
from yoni.validator.codes import orphan_domain_block, wrong_folder
from yoni.validator.models import ValidationError

_EXPECTED: dict[BlockKind, str] = {
    BlockKind.PROJECT: "project/",
    BlockKind.DOMAIN: "domains/<name>/domain.yoni",
    BlockKind.ENTITY: "domains/<name>/entities/",
    BlockKind.INTENT: "domains/<name>/intents/",
    BlockKind.RULE: "domains/<name>/rules/",
    BlockKind.QUERY: "domains/<name>/queries/",
    BlockKind.ACTION: "domains/<name>/actions/",
    BlockKind.EVENT: "domains/<name>/events/",
    BlockKind.STATE: "domains/<name>/states/",
    BlockKind.WORKFLOW: "domains/<name>/workflows/",
    BlockKind.CONSTRAINT: "domains/<name>/constraints/",
    BlockKind.ERROR: "domains/<name>/errors/",
    BlockKind.TEST: "domains/<name>/tests/",
    BlockKind.CAPABILITY: "capabilities/<name>/capability.yoni",
    BlockKind.VIEW: "views/",
    BlockKind.DEPLOYMENT: "deployments/",
    BlockKind.MIGRATION: "migrations/",
}


def _path_ok(kind: BlockKind, rel_path: str) -> bool:
    path = rel_path.replace("\\", "/")
    if kind == BlockKind.PROJECT:
        return path.startswith("project/")
    if kind == BlockKind.DOMAIN:
        return path.endswith(("/domain.yoni", "/domain.yni", "/domain.yo")) and path.startswith("domains/")
    if kind == BlockKind.CAPABILITY:
        return path.startswith("capabilities/") and path.endswith(
            ("/capability.yoni", "/capability.yni", "/capability.yo")
        )
    if kind == BlockKind.VIEW:
        return path.startswith("views/")
    if kind == BlockKind.DEPLOYMENT:
        return path.startswith("deployments/")
    if kind == BlockKind.MIGRATION:
        return path.startswith("migrations/")
    role = {
        BlockKind.ENTITY: "entities",
        BlockKind.INTENT: "intents",
        BlockKind.RULE: "rules",
        BlockKind.QUERY: "queries",
        BlockKind.ACTION: "actions",
        BlockKind.EVENT: "events",
        BlockKind.STATE: "states",
        BlockKind.WORKFLOW: "workflows",
        BlockKind.CONSTRAINT: "constraints",
        BlockKind.ERROR: "errors",
        BlockKind.TEST: "tests",
    }.get(kind)
    if role:
        return f"/{role}/" in path and path.startswith("domains/")
    return True


def check_repository(workspace: NormalizedWorkspace) -> list[ValidationError]:
    errors: list[ValidationError] = []
    domain_paths: set[str] = set()

    for block in workspace.blocks.values():
        if block.kind == BlockKind.DOMAIN and block.file.domain:
            domain_paths.add(block.file.domain)

    for block in workspace.blocks.values():
        if not _path_ok(block.kind, block.file.rel_path):
            errors.append(
                wrong_folder(
                    block.kind.value,
                    block.file.rel_path,
                    _EXPECTED.get(block.kind, ""),
                    block_id=block.block_id,
                )
            )
        if block.file.domain and block.kind not in (BlockKind.DOMAIN, BlockKind.PROJECT):
            if block.file.domain not in domain_paths:
                errors.append(
                    orphan_domain_block(
                        block.file.rel_path,
                        block.file.domain,
                        block_id=block.block_id,
                    )
                )
    return errors
