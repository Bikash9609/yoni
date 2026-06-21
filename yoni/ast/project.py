"""ProjectAST — strongly-typed AST for project blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from yoni.ast.block_base import BlockBase
from yoni.ast.expr import EnvDef
from yoni.ast.types import RefLink


class ProjectAST(BlockBase):
    type: Literal["Project"] = "Project"
    domains: list[RefLink] = Field(default_factory=list)
    capabilities: list[RefLink] = Field(default_factory=list)
    env: EnvDef | None = None
