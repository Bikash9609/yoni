"""Yoni compiler — Grammar + Parsing (step 1).

Pipeline position: .yoni files → Parser → AST
See docs/03-final-yoni-specs.md for full architecture.
"""

from yoni.ast.base import BlockKind, ParseResult, YoniBlock
from yoni.ast.entity import EntityAST
from yoni.ast.intent import IntentAST
from yoni.errors import ParseError
from yoni.parser.engine import build_parser, parse_file, parse_source

__all__ = [
    "BlockKind",
    "EntityAST",
    "IntentAST",
    "ParseError",
    "ParseResult",
    "YoniBlock",
    "build_parser",
    "parse_file",
    "parse_source",
]
