"""StateAST — strongly-typed AST for state blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from yoni.ast.block_base import BlockBase
from yoni.ast.expr import TransitionDef


class StateAST(BlockBase):
    type: Literal["State"] = "State"
    states: list[str] = Field(default_factory=list)
    transitions: list[TransitionDef] = Field(default_factory=list)
