"""MigrationAST — strongly-typed AST for migration blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from yoni.ast.block_base import BlockBase
from yoni.ast.expr import ChangeDef
from yoni.ast.types import RefLink


class MigrationAST(BlockBase):
    type: Literal["Migration"] = "Migration"
    from_version: int | None = None
    to_version: int | None = None
    changes: list[ChangeDef] = Field(default_factory=list)
    affects: list[RefLink] = Field(default_factory=list)
    breaking: bool = False
