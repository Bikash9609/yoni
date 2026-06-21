"""EventAST — strongly-typed AST for event blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from yoni.ast.block_base import BlockBase
from yoni.ast.types import FieldDef


class EventAST(BlockBase):
    type: Literal["Event"] = "Event"
    payload: list[FieldDef] = Field(default_factory=list)
