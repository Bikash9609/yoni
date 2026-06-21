"""Auto-generate stable block ids for token-minimal specs."""

from __future__ import annotations

import re

from yoni.ast.base import BlockKind

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

_CAMEL = re.compile(r"(?<=[a-z0-9])([A-Z])|([A-Z]+)(?=[A-Z][a-z])")


def _name_token(name: str) -> str:
    spaced = _CAMEL.sub(r" \1\2", name).replace("-", " ").replace("_", " ")
    return "_".join(spaced.upper().split())


def generate_block_id(
    kind: BlockKind,
    name: str,
    *,
    used: set[str],
) -> str:
    prefix = _ID_PREFIX.get(kind, "BLK_")
    base = f"{prefix}{_name_token(name)}"
    seq = 1
    while True:
        candidate = f"{base}_{seq:03d}"
        if candidate not in used:
            return candidate
        seq += 1
