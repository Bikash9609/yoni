"""Full Yoni compiler pipeline orchestrator."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from yoni.errors import ParseError
from yoni.graph.builder import build_graph
from yoni.graph.models import KnowledgeGraph
from yoni.normalizer.models import NormalizedWorkspace
from yoni.normalizer.run import normalize_workspace
from yoni.validator.models import ValidationError
from yoni.validator.run import validate_workspace
from yoni.workspace.loader import Workspace, load_workspace


class CompileResult(BaseModel):
    ok: bool = False
    parse_errors: list[ParseError] = Field(default_factory=list)
    validation_errors: list[ValidationError] = Field(default_factory=list)
    workspace: Workspace | None = None
    normalized: NormalizedWorkspace | None = None
    graph: KnowledgeGraph | None = None


def compile_workspace(root: Path | str, *, write_cache: bool = True) -> CompileResult:
    project_root = Path(root).resolve()
    workspace = load_workspace(project_root)

    if not workspace.parse_ok:
        return CompileResult(
            ok=False,
            parse_errors=workspace.parse_errors,
            workspace=workspace,
        )

    normalized = normalize_workspace(workspace)
    graph = build_graph(normalized)
    validation_errors = validate_workspace(normalized, graph, workspace)

    if write_cache:
        _write_caches(project_root, workspace, normalized, graph)

    ok = not any(error.severity == "error" for error in validation_errors)
    return CompileResult(
        ok=ok,
        validation_errors=validation_errors,
        workspace=workspace,
        normalized=normalized,
        graph=graph,
    )


def _write_caches(
    root: Path,
    workspace: Workspace,
    normalized: NormalizedWorkspace,
    graph: KnowledgeGraph,
) -> None:
    cache = root / ".ai" / "cache"
    ast_root = cache / "ast"
    for item in workspace.files:
        rel = Path(item.rel_path)
        out = ast_root / rel.with_suffix(".json")
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "file": item.rel_path,
            "ok": item.result.ok,
            "errors": [error.model_dump() for error in item.result.errors],
            "ast": item.result.ast.model_dump() if item.result.ast else None,
        }
        out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    norm_path = cache / "normalized" / "normalized.json"
    norm_path.parent.mkdir(parents=True, exist_ok=True)
    norm_path.write_text(
        json.dumps(normalized.model_dump(), indent=2) + "\n",
        encoding="utf-8",
    )

    graph_path = cache / "graph" / "graph.json"
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph_path.write_text(
        json.dumps(graph.model_dump(), indent=2) + "\n",
        encoding="utf-8",
    )
