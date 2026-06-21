"""DeploymentAST — strongly-typed AST for deployment blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from yoni.ast.expr import EnvDef
from yoni.ast.types import Reference, SourceSpan


class DeploymentAST(BaseModel):
    type: Literal["Deployment"] = "Deployment"
    id: str
    name: str
    version: int = 1
    desc: str = ""
    region: str = ""
    replicas: int | None = None
    resources: dict[str, str | int | float] = Field(default_factory=dict)
    services: list[Reference] = Field(default_factory=list)
    env: EnvDef | None = None
    span: SourceSpan | None = None
