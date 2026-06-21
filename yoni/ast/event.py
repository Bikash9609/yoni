"""EventAST — strongly-typed AST for event blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from yoni.ast.types import FieldDef, SourceSpan


class EventAST(BaseModel):
    type: Literal["Event"] = "Event"
    id: str
    name: str
    version: int = 1
    desc: str = ""
    payload: list[FieldDef] = Field(default_factory=list)
    span: SourceSpan | None = None
