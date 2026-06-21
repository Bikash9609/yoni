"""Build NormalizedWorkspace from parsed project files."""

from __future__ import annotations

from yoni.ast.base import BlockKind
from yoni.normalizer.blocks import block_kind, normalize_body
from yoni.normalizer.models import FileContext, NormalizedBlock, NormalizedWorkspace
from yoni.normalizer.path import infer_file_context
from yoni.normalizer.refs import extract_refs
from yoni.workspace.loader import Workspace

_SYMBOL_KIND: dict[BlockKind, str] = {
    BlockKind.PROJECT: "Project",
    BlockKind.DOMAIN: "Domain",
    BlockKind.ENTITY: "Entity",
    BlockKind.STATE: "State",
    BlockKind.EVENT: "Event",
    BlockKind.INTENT: "Intent",
    BlockKind.RULE: "Rule",
    BlockKind.QUERY: "Query",
    BlockKind.ACTION: "Action",
    BlockKind.CONSTRAINT: "Constraint",
    BlockKind.WORKFLOW: "Workflow",
    BlockKind.ERROR: "Error",
    BlockKind.TEST: "Test",
    BlockKind.CAPABILITY: "Capability",
    BlockKind.VIEW: "View",
    BlockKind.DEPLOYMENT: "Deployment",
    BlockKind.MIGRATION: "Migration",
}


_GLOBAL_KINDS = frozenset(
    {
        BlockKind.PROJECT,
        BlockKind.DOMAIN,
        BlockKind.CAPABILITY,
        BlockKind.VIEW,
        BlockKind.DEPLOYMENT,
        BlockKind.MIGRATION,
    }
)


def normalize_workspace(workspace: Workspace) -> NormalizedWorkspace:
    blocks: dict[str, NormalizedBlock] = {}
    symbols: dict[str, str] = {}

    for item in workspace.files:
        ast = item.result.ast
        if ast is None:
            continue
        kind = block_kind(ast)
        domain, folder_role = infer_file_context(item.rel_path)
        block = NormalizedBlock(
            block_id=ast.id.upper(),
            kind=kind,
            name=ast.name,
            desc=ast.desc.strip(),
            version=ast.version or 1,
            file=FileContext(
                rel_path=item.rel_path,
                domain=domain,
                folder_role=folder_role,
            ),
            body=normalize_body(ast),
            refs=extract_refs(ast),
        )
        blocks[block.block_id] = block
        symbol_kind = _SYMBOL_KIND.get(kind, kind.value.title())
        base_key = f"{symbol_kind}.{ast.name}"
        if kind in _GLOBAL_KINDS:
            symbols[base_key] = block.block_id
        elif domain:
            symbols[f"{domain}:{base_key}"] = block.block_id
        else:
            symbols[base_key] = block.block_id

    return NormalizedWorkspace(root=workspace.root, blocks=blocks, symbols=symbols)
