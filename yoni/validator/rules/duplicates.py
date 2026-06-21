"""Duplicate id and symbol validation."""

from __future__ import annotations

from yoni.normalizer.blocks import block_kind
from yoni.normalizer.models import NormalizedWorkspace
from yoni.normalizer.path import infer_file_context
from yoni.validator.codes import duplicate_block_id, duplicate_symbol
from yoni.validator.models import ValidationError
from yoni.workspace.loader import Workspace

_SYMBOL_KIND = {
    "project": "Project",
    "domain": "Domain",
    "entity": "Entity",
    "state": "State",
    "event": "Event",
    "intent": "Intent",
    "rule": "Rule",
    "query": "Query",
    "action": "Action",
    "constraint": "Constraint",
    "workflow": "Workflow",
    "error": "Error",
    "test": "Test",
    "capability": "Capability",
    "view": "View",
    "deployment": "Deployment",
    "migration": "Migration",
}


def check_duplicates(
    workspace: NormalizedWorkspace,
    source: Workspace | None = None,
) -> list[ValidationError]:
    errors: list[ValidationError] = []
    id_files: dict[str, str] = {}
    symbol_map: dict[str, str] = {}

    scan = source.files if source else []
    for item in scan:
        ast = item.result.ast
        if ast is None:
            continue
        block_id = ast.id.upper()
        prev_file = id_files.get(block_id)
        if prev_file and prev_file != item.rel_path:
            errors.append(
                duplicate_block_id(
                    block_id,
                    file=item.rel_path,
                    other_file=prev_file,
                )
            )
        id_files.setdefault(block_id, item.rel_path)

        kind = block_kind(ast)
        domain, _ = infer_file_context(item.rel_path)
        symbol_kind = _SYMBOL_KIND.get(kind.value, kind.value.title())
        base = f"{symbol_kind}.{ast.name}"
        symbol = f"{domain}:{base}" if domain else base
        other_id = symbol_map.get(symbol)
        if other_id and other_id != block_id:
            errors.append(
                duplicate_symbol(
                    symbol,
                    block_id,
                    other_id,
                    file=item.rel_path,
                )
            )
        symbol_map.setdefault(symbol, block_id)

    return errors
