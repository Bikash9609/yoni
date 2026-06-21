"""Token stream from Yoni source — decoupled from parse/transform."""

from __future__ import annotations

from dataclasses import dataclass

from lark import Token

from yoni.parser.engine import build_parser
from yoni.parser.indenter import YoniIndenter


@dataclass(frozen=True)
class TokenInfo:
    type: str
    value: str
    line: int
    column: int
    end_line: int
    end_column: int


_SKIP = frozenset({"_NEWLINE", "$END"})


def tokenize(source: str) -> list[TokenInfo]:
    """Return a flat token stream for *source* (indent tokens included)."""
    parser, indenter = build_parser()
    indenter.tab_errors.clear()
    tokens: list[TokenInfo] = []
    for tok in parser.lex(source):
        if not isinstance(tok, Token):
            continue
        if tok.type in _SKIP:
            continue
        tokens.append(
            TokenInfo(
                type=tok.type,
                value=str(tok),
                line=tok.line or 0,
                column=tok.column or 0,
                end_line=getattr(tok, "end_line", None) or tok.line or 0,
                end_column=getattr(tok, "end_column", None) or tok.column or 0,
            )
        )
    return tokens
