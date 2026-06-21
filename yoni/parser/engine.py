"""Lark parser engine for Yoni source files."""

from __future__ import annotations

from functools import lru_cache
from importlib import resources
from pathlib import Path

from lark import Lark
from lark.exceptions import LarkError, UnexpectedCharacters, UnexpectedToken

from yoni.ast.base import ParseResult, YoniBlock
from yoni.errors import syntax_error, tab_in_indent, unexpected_token
from yoni.parser.indenter import YoniIndenter
from yoni.parser.transformer import YoniTransformer

GRAMMAR_PACKAGE = "yoni.grammar"
GRAMMAR_FILE = "yoni.lark"


@lru_cache(maxsize=1)
def build_parser() -> tuple[Lark, YoniIndenter]:
    """Load yoni.lark and return a reusable Lark parser with indentation support."""
    grammar_dir = resources.files(GRAMMAR_PACKAGE)
    grammar_text = grammar_dir.joinpath(GRAMMAR_FILE).read_text(encoding="utf-8")
    indenter = YoniIndenter()
    parser = Lark(
        grammar_text,
        start="start",
        parser="lalr",
        postlex=indenter,
        propagate_positions=True,
        import_paths=[str(grammar_dir)],
    )
    return parser, indenter


def parse_source(source: str, *, file: str = "<stdin>") -> ParseResult[YoniBlock]:
    """Parse Yoni source text and return AST + diagnostics."""
    parser, indenter = build_parser()
    indenter.tab_errors.clear()
    try:
        tree = parser.parse(source)
    except UnexpectedToken as exc:
        expected = ", ".join(sorted(exc.expected)) if exc.expected else None
        token_text = str(exc.token) if exc.token else "?"
        return ParseResult(
            ast=None,
            errors=[
                syntax_error(
                    f"Unexpected token {token_text!r} at line {exc.line}, column {exc.column}."
                    + (f" Expected: {expected}." if expected else ""),
                    file=file,
                    line=exc.line,
                    column=exc.column,
                )
            ],
            source=source,
            file=file,
        )
    except UnexpectedCharacters as exc:
        return ParseResult(
            ast=None,
            errors=[
                unexpected_token(
                    exc.char,
                    file=file,
                    line=exc.line,
                    column=exc.column,
                )
            ],
            source=source,
            file=file,
        )
    except LarkError as exc:
        return ParseResult(
            ast=None,
            errors=[syntax_error(str(exc), file=file)],
            source=source,
            file=file,
        )

    errors = []
    for line_no, _ in indenter.tab_errors:
        errors.append(tab_in_indent(file=file, line=line_no))

    transformer = YoniTransformer(file=file)
    ast, parse_errors = transformer.transform(tree)
    return ParseResult(
        ast=ast,
        errors=errors + parse_errors,
        source=source,
        file=file,
    )


def parse_file(path: Path | str) -> ParseResult[YoniBlock]:
    """Read a .yoni file and parse it."""
    file_path = Path(path)
    source = file_path.read_text(encoding="utf-8")
    return parse_source(source, file=str(file_path))
