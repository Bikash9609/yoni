"""EntityAST — strongly-typed AST for entity blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from yoni.ast.block_base import BlockBase
from yoni.ast.types import FieldDef, IndexDef


class EntityAST(BlockBase):
    """AST node for `entity` blocks."""

    type: Literal["Entity"] = "Entity"
    fields: list[FieldDef] = Field(default_factory=list)
    indices: list[IndexDef] = Field(default_factory=list)
