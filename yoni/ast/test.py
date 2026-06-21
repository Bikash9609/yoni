"""TestAST — strongly-typed AST for test blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from yoni.ast.expr import ExpectOp, ProcessOp, WhenDef
from yoni.ast.types import SourceSpan


class TestAST(BaseModel):
    type: Literal["Test"] = "Test"
    id: str
    name: str
    version: int = 1
    desc: str = ""
    given: list[ProcessOp] = Field(default_factory=list)
    when: WhenDef | None = None
    expect: list[ExpectOp] = Field(default_factory=list)
    span: SourceSpan | None = None
