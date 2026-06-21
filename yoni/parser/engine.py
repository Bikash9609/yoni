"""Lark parser engine for Yoni source files."""

from __future__ import annotations

from functools import lru_cache
from importlib import resources
from pathlib import Path

from lark import Lark
from lark.exceptions import LarkError

from yoni.ast.base import ParseResult, YoniBlock
from yoni.errors import syntax_error
from yoni.parser.indenter import YoniIndenter
from yoni.parser.transformer import YoniTransformer

GRAMMAR_PACKAGE = "yoni.grammar"
GRAMMAR_FILE = "yoni.lark"


@lru_cache(maxsize=1)
def build_parser() -> Lark:
    """Load yoni.lark and return a reusable Lark parser with indentation support."""
    grammar_dir = resources.files(GRAMMAR_PACKAGE)
    grammar_text = grammar_dir.joinpath(GRAMMAR_FILE).read_text(encoding="utf-8")
    return Lark(
        grammar_text,
        start="start",
        parser="lalr",
        postlex=YoniIndenter(),
        propagate_positions=True,
        import_paths=[str(grammar_dir)],
    )


def parse_source(source: str, *, file: str = "<stdin>") -> ParseResult[YoniBlock]:
    """Parse Yoni source text and return AST + diagnostics."""
    parser = build_parser()
    try:
        tree = parser.parse(source)
    except LarkError as exc:
        return ParseResult(
            ast=None,
            errors=[syntax_error(str(exc), file=file)],
            source=source,
            file=file,
        )

    transformer = YoniTransformer(file=file)
    ast, errors = transformer.transform(tree)
    return ParseResult(ast=ast, errors=errors, source=source, file=file)


def parse_file(path: Path | str) -> ParseResult[YoniBlock]:
    """Read a .yoni file and parse it."""
    file_path = Path(path)
    source = file_path.read_text(encoding="utf-8")
    return parse_source(source, file=str(file_path))
