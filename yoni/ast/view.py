"""ViewAST — strongly-typed AST for view blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from yoni.ast.block_base import BlockBase
from yoni.ast.expr import LayoutDef
from yoni.ast.types import RefLink


class ViewAST(BlockBase):
    type: Literal["View"] = "View"
    query: RefLink | None = None
    fields: list[str] = Field(default_factory=list)
    actions: list[RefLink] = Field(default_factory=list)
    layout: LayoutDef | None = None
