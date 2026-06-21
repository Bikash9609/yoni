"""Build NormalizedWorkspace from parsed project files."""

from __future__ import annotations

from yoni.ast.base import BlockKind, YoniBlock
from yoni.normalizer.blocks import block_kind, normalize_body
from yoni.normalizer.canonical import order_body, resolve_body_refs
from yoni.normalizer.ids import generate_block_id
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


def _ensure_block_id(ast: YoniBlock, kind: BlockKind, used: set[str]) -> str:
    raw = (ast.id or "").strip()
    if raw:
        return raw.upper()
    return generate_block_id(kind, ast.name, used=used)


def normalize_workspace(workspace: Workspace) -> NormalizedWorkspace:
    blocks: dict[str, NormalizedBlock] = {}
    symbols: dict[str, str] = {}
    used_ids: set[str] = set()

    staged: list[tuple[object, BlockKind, str, str, str | None, str | None]] = []
    for item in workspace.files:
        ast = item.result.ast
        if ast is None:
            continue
        kind = block_kind(ast)
        domain, folder_role = infer_file_context(item.rel_path)
        block_id = _ensure_block_id(ast, kind, used_ids)
        used_ids.add(block_id)
        staged.append((ast, kind, block_id, item.rel_path, domain, folder_role))

    for ast, kind, block_id, rel_path, domain, folder_role in staged:
        body = normalize_body(ast)
        body = order_body(kind, body)
        block = NormalizedBlock(
            block_id=block_id,
            kind=kind,
            name=ast.name,
            desc=(ast.desc or "").strip(),
            version=ast.version or 1,
            file=FileContext(
                rel_path=rel_path,
                domain=domain,
                folder_role=folder_role,
            ),
            body=body,
            refs=extract_refs(ast),
            ast_ref=f"{rel_path}#{block_id}",
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

    norm = NormalizedWorkspace(root=workspace.root, blocks=blocks, symbols=symbols)
    for block in norm.blocks.values():
        block.body = resolve_body_refs(
            block.body,
            norm,
            domain=block.file.domain,
        )
    return norm
