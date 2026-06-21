"""Field type compatibility validation."""

from __future__ import annotations

from yoni.ast.base import BlockKind
from yoni.graph.models import KnowledgeGraph
from yoni.normalizer.models import NormalizedWorkspace
from yoni.validator.models import ValidationError

_SCALAR = frozenset({"string", "integer", "float", "boolean", "timestamp"})


def check_field_types(
    workspace: NormalizedWorkspace,
    graph: KnowledgeGraph,
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for block in workspace.blocks.values():
        if block.kind not in (BlockKind.ENTITY, BlockKind.INTENT, BlockKind.EVENT):
            continue
        key = "fields" if block.kind == BlockKind.ENTITY else "inputs"
        if block.kind == BlockKind.EVENT:
            key = "payload"
        for field in block.body.get(key, []):
            type_name = field.get("type", "")
            ref = field.get("ref")
            if field.get("type_code") is not None:
                continue
            if ref and type_name not in _SCALAR:
                block_id = ref.get("block_id")
                if block_id and block_id not in graph.nodes:
                    errors.append(
                        ValidationError(
                            code="YONI3002",
                            message=f"Field {field.get('name')!r} references unknown type {type_name}",
                            file=block.file.rel_path,
                            block_id=block.block_id,
                            suggestion="Define the referenced entity or use a scalar type code.",
                        )
                    )
            elif not ref and type_name not in _SCALAR and type_name != "unknown":
                errors.append(
                    ValidationError(
                        code="YONI3002",
                        message=f"Field {field.get('name')!r} has incompatible type {type_name!r}",
                        file=block.file.rel_path,
                        block_id=block.block_id,
                        suggestion="Use s/i/f/b/t or @Entity.Name for field type.",
                    )
                )
    return errors
