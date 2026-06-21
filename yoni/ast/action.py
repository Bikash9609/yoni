"""ActionAST — strongly-typed AST for action blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from yoni.ast.types import FieldDef, Reference, SourceSpan


class ActionAST(BaseModel):
    type: Literal["Action"] = "Action"
    id: str
    name: str
    version: int = 1
    desc: str = ""
    uses: Reference | None = None
    inputs: list[FieldDef] = Field(default_factory=list)
    result: list[FieldDef] = Field(default_factory=list)
    span: SourceSpan | None = None
