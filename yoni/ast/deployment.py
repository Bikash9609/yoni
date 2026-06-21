"""DeploymentAST — strongly-typed AST for deployment blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from yoni.ast.block_base import BlockBase
from yoni.ast.expr import EnvDef
from yoni.ast.types import RefLink


class DeploymentAST(BlockBase):
    type: Literal["Deployment"] = "Deployment"
    region: str = ""
    replicas: int | None = None
    resources: dict[str, str | int | float] = Field(default_factory=dict)
    services: list[RefLink] = Field(default_factory=list)
    env: EnvDef | None = None
