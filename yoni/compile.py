"""Parse a Yoni project tree and write AST snapshots to .ai/cache/ast/.

Parses all 17 block kinds into strongly-typed AST JSON.
"""

from __future__ import annotations

import json
from pathlib import Path

from yoni.parser.engine import parse_file


def compile_project(root: Path | str) -> tuple[int, int]:
    """Parse every .yoni file under root and mirror AST JSON under .ai/cache/ast/."""
    project_root = Path(root)
    ast_root = project_root / ".ai" / "cache" / "ast"
    ok_count = 0
    total = 0

    for source in sorted(project_root.rglob("*.yoni")):
        if ".ai" in source.parts:
            continue
        total += 1
        rel = source.relative_to(project_root)
        out = ast_root / rel.with_suffix(".json")
        out.parent.mkdir(parents=True, exist_ok=True)

        result = parse_file(source)
        payload = {
            "file": str(rel),
            "ok": result.ok,
            "errors": [error.model_dump() for error in result.errors],
            "ast": result.ast.model_dump() if result.ast else None,
        }
        out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        if result.ok:
            ok_count += 1

    return ok_count, total


def main(argv: list[str] | None = None) -> int:
    import sys

    args = argv if argv is not None else sys.argv[1:]
    root = Path(args[0]) if args else Path("samples/invoicing")
    ok_count, total = compile_project(root)
    print(f"compiled {ok_count}/{total} -> {root / '.ai' / 'cache' / 'ast'}")
    return 0 if ok_count == total else 1
