"""Parse a Yoni project tree and write compiler cache artifacts."""

from __future__ import annotations

from pathlib import Path

from yoni.pipeline import compile_workspace


def compile_project(root: Path | str) -> tuple[int, int]:
    """Compile project: parse, normalize, graph, validate; write .ai/cache/."""
    project_root = Path(root)
    result = compile_workspace(project_root, write_cache=True)
    total = len(result.workspace.files) if result.workspace else 0
    if not result.workspace or not result.workspace.parse_ok:
        parse_ok = sum(1 for f in result.workspace.files if f.result.ok) if result.workspace else 0
        return parse_ok, total
    ok_count = total if result.ok else total - len(
        [e for e in result.validation_errors if e.severity == "error"]
    )
    if result.ok:
        ok_count = total
    else:
        ok_count = max(0, total - len(result.validation_errors))
    return (total if result.ok else ok_count, total)


def main(argv: list[str] | None = None) -> int:
    import sys

    args = argv if argv is not None else sys.argv[1:]
    root = Path(args[0]) if args else Path("samples/invoicing")
    result = compile_workspace(root, write_cache=True)
    total = len(result.workspace.files) if result.workspace else 0
    cache = root / ".ai" / "cache"
    if not result.workspace or not result.workspace.parse_ok:
        parse_ok = sum(1 for f in result.workspace.files if f.result.ok) if result.workspace else 0
        print(f"compiled {parse_ok}/{total} -> {cache / 'ast'} (parse errors)")
        return 1
    if result.ok:
        print(
            f"compiled {total}/{total} -> {cache} "
            f"(ast, normalized, graph)"
        )
        return 0
    err_count = len([e for e in result.validation_errors if e.severity == "error"])
    print(f"compiled {total}/{total} with {err_count} validation errors -> {cache}")
    return 1
