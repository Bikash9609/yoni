"""State machine and transition validation."""

from __future__ import annotations

from yoni.ast.base import BlockKind
from yoni.normalizer.models import NormalizedWorkspace
from yoni.validator.models import ValidationError


def check_state_machine(workspace: NormalizedWorkspace) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for block in workspace.blocks.values():
        if block.kind != BlockKind.STATE:
            continue
        states = set(block.body.get("states", []))
        for transition in block.body.get("transitions", []):
            src = transition.get("from") or transition.get("source")
            dst = transition.get("to") or transition.get("target")
            for label, name in (("from", src), ("to", dst)):
                if name and name not in states:
                    errors.append(
                        ValidationError(
                            code="YONI3004",
                            message=f"Transition {label} state {name!r} not declared in states",
                            file=block.file.rel_path,
                            block_id=block.block_id,
                            suggestion=f"Add {name} to states: or fix the transition.",
                        )
                    )
    return errors
