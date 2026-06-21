"""ProjectAST — strongly-typed AST for project blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from yoni.ast.expr import EnvDef
from yoni.ast.types import Reference, SourceSpan


class ProjectAST(BaseModel):
    type: Literal["Project"] = "Project"
    id: str
    name: str
    version: int = 1
    desc: str = ""
    domains: list[Reference] = Field(default_factory=list)
    capabilities: list[Reference] = Field(default_factory=list)
    env: EnvDef | None = None
    span: SourceSpan | None = None
