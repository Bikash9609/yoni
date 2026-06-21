"""StateAST — strongly-typed AST for state blocks."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from yoni.ast.expr import TransitionDef
from yoni.ast.types import SourceSpan


class StateAST(BaseModel):
    type: Literal["State"] = "State"
    id: str
    name: str
    version: int = 1
    desc: str = ""
    states: list[str] = Field(default_factory=list)
    transitions: list[TransitionDef] = Field(default_factory=list)
    span: SourceSpan | None = None
