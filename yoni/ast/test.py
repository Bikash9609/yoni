"""TestAST — strongly-typed AST for test blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from yoni.ast.block_base import BlockBase
from yoni.ast.expr import ExpectOp, ProcessOp, WhenDef


class TestAST(BlockBase):
    type: Literal["Test"] = "Test"
    given: list[ProcessOp] = Field(default_factory=list)
    when: WhenDef | None = None
    expect: list[ExpectOp] = Field(default_factory=list)
