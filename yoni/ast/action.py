"""ActionAST — strongly-typed AST for action blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from yoni.ast.block_base import BlockBase
from yoni.ast.types import FieldDef, RefLink


class ActionAST(BlockBase):
    type: Literal["Action"] = "Action"
    uses: RefLink | None = None
    inputs: list[FieldDef] = Field(default_factory=list)
    result: list[FieldDef] = Field(default_factory=list)
