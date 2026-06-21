"""Capability binding and env config validation."""

from __future__ import annotations

from yoni.ast.base import BlockKind
from yoni.normalizer.models import NormalizedWorkspace
from yoni.validator.models import ValidationError


def check_capability_binding(workspace: NormalizedWorkspace) -> list[ValidationError]:
    errors: list[ValidationError] = []
    cap_config: dict[str, set[str]] = {}
    for block in workspace.blocks.values():
        if block.kind == BlockKind.CAPABILITY:
            cap_config[block.name] = {
                f.get("name", "") for f in block.body.get("config", [])
            }

    for block in workspace.blocks.values():
        if block.kind not in (BlockKind.DEPLOYMENT, BlockKind.PROJECT):
            continue
        env = block.body.get("env") or {}
        entries = env.get("entries", env) if isinstance(env, dict) else {}
        if not isinstance(entries, dict):
            continue
        for key in entries:
            if "." not in key:
                continue
            cap_name, field_name = key.split(".", 1)
            known = cap_config.get(cap_name)
            if known is None:
                errors.append(
                    ValidationError(
                        code="YONI3005",
                        message=f"Env key {key!r} references unknown capability {cap_name!r}",
                        file=block.file.rel_path,
                        block_id=block.block_id,
                        suggestion="Declare the capability or fix the env key.",
                    )
                )
            elif field_name not in known:
                errors.append(
                    ValidationError(
                        code="YONI3005",
                        message=f"Env key {key!r} is not in capability {cap_name} config",
                        file=block.file.rel_path,
                        block_id=block.block_id,
                        suggestion=f"Add {field_name} to capability {cap_name} config: section.",
                    )
                )
    return errors
