"""EntityAST — strongly-typed AST for entity blocks.

Schema: docs/03-final-yoni-specs.md § EntityAST
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from yoni.ast.types import FieldDef, IndexDef, SourceSpan


class EntityAST(BaseModel):
    """AST node for `entity` blocks."""

    type: Literal["Entity"] = "Entity"
    id: str
    name: str
    version: int = 1
    desc: str = ""
    fields: list[FieldDef] = []
    indices: list[IndexDef] = []
    span: SourceSpan | None = None
