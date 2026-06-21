"""ViewAST — strongly-typed AST for view blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from yoni.ast.expr import LayoutDef
from yoni.ast.types import Reference, SourceSpan


class ViewAST(BaseModel):
    type: Literal["View"] = "View"
    id: str
    name: str
    version: int = 1
    desc: str = ""
    query: Reference | None = None
    fields: list[str] = Field(default_factory=list)
    actions: list[Reference] = Field(default_factory=list)
    layout: LayoutDef | None = None
    span: SourceSpan | None = None
