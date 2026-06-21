"""CapabilityAST — strongly-typed AST for capability blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from yoni.ast.types import FieldDef, Reference, SourceSpan


class CapabilityAST(BaseModel):
    type: Literal["Capability"] = "Capability"
    id: str
    name: str
    version: int = 1
    desc: str = ""
    actions: list[Reference] = Field(default_factory=list)
    config: list[FieldDef] = Field(default_factory=list)
    span: SourceSpan | None = None
