"""Process op semantic validation."""

from __future__ import annotations

from yoni.ast.base import BlockKind
from yoni.graph.models import KnowledgeGraph
from yoni.normalizer.models import NormalizedWorkspace
from yoni.validator.models import ValidationError

_VALID_OPS = frozenset({"new", "set", "save"})


def check_process_ops(
    workspace: NormalizedWorkspace,
    graph: KnowledgeGraph,
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for block in workspace.blocks.values():
        if block.kind != BlockKind.INTENT:
            continue
        for step in block.body.get("process", []):
            op = step.get("op", "")
            if op not in _VALID_OPS:
                errors.append(
                    ValidationError(
                        code="YONI3003",
                        message=f"Unknown process op {op!r}",
                        file=block.file.rel_path,
                        block_id=block.block_id,
                        suggestion="Use new, set, or save.",
                    )
                )
                continue
            if op == "new":
                target = step.get("target")
                type_ref = step.get("type_ref")
                if not target or not type_ref:
                    errors.append(
                        ValidationError(
                            code="YONI3003",
                            message="Process new requires target and entity type",
                            file=block.file.rel_path,
                            block_id=block.block_id,
                            suggestion="Use: new <var> @Entity.Name",
                        )
                    )
                elif type_ref.get("block_id") and type_ref["block_id"] not in graph.nodes:
                    errors.append(
                        ValidationError(
                            code="YONI3003",
                            message=f"Process new references unknown entity",
                            file=block.file.rel_path,
                            block_id=block.block_id,
                            suggestion="Reference a defined entity block.",
                        )
                    )
            elif op in {"set", "save"} and not step.get("target"):
                errors.append(
                    ValidationError(
                        code="YONI3003",
                        message=f"Process {op} requires a target",
                        file=block.file.rel_path,
                        block_id=block.block_id,
                        suggestion=f"Use: {op} <target>",
                    )
                )
    return errors
