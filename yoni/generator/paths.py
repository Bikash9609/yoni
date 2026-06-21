"""Artifact output paths for generation jobs."""

from __future__ import annotations

import re

from yoni.ast.base import BlockKind
from yoni.normalizer.models import NormalizedBlock, NormalizedWorkspace
from yoni.planner.models import JobType

_JOB_DIR: dict[JobType, str] = {
    JobType.ENTITY_SCHEMA: "entities",
    JobType.STATE_MACHINE: "states",
    JobType.RULE_IMPL: "rules",
    JobType.CONSTRAINT_IMPL: "constraints",
    JobType.QUERY_IMPL: "queries",
    JobType.ACTION_IMPL: "actions",
    JobType.ERROR_DEF: "errors",
    JobType.INTENT_HANDLER: "intents",
}

_BLOCK_KIND_DIR: dict[BlockKind, str] = {
    BlockKind.ENTITY: "entities",
    BlockKind.STATE: "states",
    BlockKind.RULE: "rules",
    BlockKind.CONSTRAINT: "constraints",
    BlockKind.QUERY: "queries",
    BlockKind.ACTION: "actions",
    BlockKind.ERROR: "errors",
    BlockKind.INTENT: "intents",
}


def _kebab(name: str) -> str:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", name)
    spaced = spaced.replace("_", "-")
    return re.sub(r"[^a-z0-9-]+", "-", spaced.lower()).strip("-")


def artifact_path(
    job_type: JobType,
    block: NormalizedBlock,
    *,
    stack: str = "python",
) -> str:
    """Deterministic generated artifact path for a job."""
    folder = _JOB_DIR.get(job_type)
    if folder is None:
        folder = _BLOCK_KIND_DIR.get(block.kind, "misc")
    ext = _extension(stack)
    filename = f"{_kebab(block.name)}{ext}"
    return f"generated/{folder}/{filename}"


def _extension(stack: str) -> str:
    normalized = stack.lower()
    if normalized in {"python", "py"}:
        return ".py"
    if normalized in {"typescript", "ts"}:
        return ".ts"
    if normalized in {"javascript", "js"}:
        return ".js"
    if normalized == "sql":
        return ".sql"
    return ".py"
