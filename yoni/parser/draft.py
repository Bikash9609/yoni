"""Mutable accumulator while walking a parse tree."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from yoni.ast.base import BlockKind
from yoni.ast.types import SourceSpan
from yoni.errors import ParseError


@dataclass
class BlockDraft:
    kind: BlockKind
    name: str
    block_id: str | None = None
    desc: str = ""
    sections: dict[str, list[Any]] = field(default_factory=dict)
    scalars: dict[str, Any] = field(default_factory=dict)
    errors: list[ParseError] = field(default_factory=list)
    file: str = ""
    span: SourceSpan | None = None
