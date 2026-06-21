"""Policy layer compliance checks (spec §8)."""

from __future__ import annotations

from yoni.normalizer.models import NormalizedWorkspace
from yoni.validator.models import ValidationError


def check_policy(workspace: NormalizedWorkspace) -> list[ValidationError]:
    """Validate policy rules declared on entity fields (can_be_stored, etc.)."""
    errors: list[ValidationError] = []
    for block in workspace.blocks.values():
        if block.kind.value != "entity":
            continue
        for field in block.body.get("fields", []):
            for flag in ("can_be_stored", "can_be_logged", "can_be_exported"):
                if flag not in field:
                    continue
                value = field[flag]
                if not isinstance(value, bool):
                    errors.append(
                        ValidationError(
                            code="YONI3001",
                            message=f"Policy flag {flag!r} on {field.get('name')} must be boolean",
                            file=block.file.rel_path,
                            block_id=block.block_id,
                            suggestion=f"Set {flag}: true or false on the field.",
                        )
                    )
    return errors
