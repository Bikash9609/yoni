"""MigrationAST — strongly-typed AST for migration blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from yoni.ast.expr import ChangeDef
from yoni.ast.types import Reference, SourceSpan


class MigrationAST(BaseModel):
    type: Literal["Migration"] = "Migration"
    id: str
    name: str
    version: int = 1
    desc: str = ""
    from_version: int | None = None
    to_version: int | None = None
    changes: list[ChangeDef] = Field(default_factory=list)
    affects: list[Reference] = Field(default_factory=list)
    breaking: bool = False
    span: SourceSpan | None = None
