"""ID prefix and filename naming validation."""

from __future__ import annotations

import re

from yoni.ast.base import BlockKind
from yoni.normalizer.models import NormalizedWorkspace
from yoni.validator.codes import non_kebab_filename, wrong_id_prefix
from yoni.validator.models import ValidationError

_ID_PREFIX: dict[BlockKind, str] = {
    BlockKind.PROJECT: "PROJ_",
    BlockKind.DOMAIN: "DOM_",
    BlockKind.ENTITY: "ENT_",
    BlockKind.STATE: "STS_",
    BlockKind.RULE: "RULE_",
    BlockKind.QUERY: "QUERY_",
    BlockKind.INTENT: "INT_",
    BlockKind.ACTION: "ACT_",
    BlockKind.EVENT: "EVT_",
    BlockKind.WORKFLOW: "WF_",
    BlockKind.CONSTRAINT: "CNST_",
    BlockKind.ERROR: "ERR_",
    BlockKind.TEST: "TST_",
    BlockKind.CAPABILITY: "CAP_",
    BlockKind.VIEW: "VIEW_",
    BlockKind.DEPLOYMENT: "DEP_",
    BlockKind.MIGRATION: "MIG_",
}

_KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*\.(yoni|yni|yo)$")
_DOMAIN_FILES = frozenset({"domain.yoni", "domain.yni", "domain.yo"})
_CAPABILITY_FILES = frozenset({"capability.yoni", "capability.yni", "capability.yo"})


def check_naming(workspace: NormalizedWorkspace) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for block in workspace.blocks.values():
        prefix = _ID_PREFIX.get(block.kind)
        if prefix and not block.block_id.startswith(prefix):
            errors.append(
                wrong_id_prefix(
                    block.block_id,
                    prefix,
                    file=block.file.rel_path,
                )
            )
        filename = block.file.rel_path.rsplit("/", 1)[-1]
        if filename not in _DOMAIN_FILES and filename not in _CAPABILITY_FILES:
            if not _KEBAB.match(filename):
                errors.append(
                    non_kebab_filename(
                        filename,
                        file=block.file.rel_path,
                        block_id=block.block_id,
                    )
                )
    return errors
