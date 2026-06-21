"""DomainAST — strongly-typed AST for domain blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from yoni.ast.types import Reference, SourceSpan


class DomainAST(BaseModel):
    type: Literal["Domain"] = "Domain"
    id: str
    name: str
    version: int = 1
    desc: str = ""
    entities: list[Reference] = Field(default_factory=list)
    rules: list[Reference] = Field(default_factory=list)
    events: list[Reference] = Field(default_factory=list)
    span: SourceSpan | None = None
